import { JupyterFrontEnd } from '@jupyterlab/application';
import {
  Dialog,
  ICommandPalette,
  showDialog,
  showErrorMessage
} from '@jupyterlab/apputils';
import { IStateDB, PathExt, URLExt } from '@jupyterlab/coreutils';
import { FileDialog, IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { ILauncher } from '@jupyterlab/launcher';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { Contents } from '@jupyterlab/services';
import { IStatusBar } from '@jupyterlab/statusbar';
import { CommandRegistry } from '@phosphor/commands';
import { JSONExt, ReadonlyJSONObject } from '@phosphor/coreutils';
import { Signal } from '@phosphor/signaling';
import { Menu } from '@phosphor/widgets';
import JSONSchemaBridge from 'uniforms-bridge-json-schema';
import { showForm } from './form';
import { requestAPI } from './jupyter-project';
import { createProjectStatus } from './statusbar';
import {
  CommandIDs,
  IProjectManager,
  PluginID,
  Project,
  Templates
} from './tokens';
import { createValidator } from './validator';

/**
 * Project manager state ID
 */
const StateID = `${PluginID}:project`;

/**
 * Namespace of foreign command IDs used
 */
namespace ForeignCommandIDs {
  export const closeAll = 'application:close-all';
  export const goTo = 'filebrowser:go-to-path';
  export const openPath = 'filebrowser:open-path';
  export const saveAll = 'docmanager:save-all';
}

/**
 * Project Manager
 */
class ProjectManager implements IProjectManager {
  /**
   * Project Manager constructor
   *
   * @param settings Project template settings
   * @param state Application state handler
   * @param appRestored Promise that resolve when the application is restored
   */
  constructor(
    settings: Templates.IProject,
    state: IStateDB,
    appRestored: Promise<void>
  ) {
    this._configurationFilename = settings.configurationFilename;
    this._state = state;

    if (settings.defaultPath) {
      this._defaultPath = settings.defaultPath;
    }

    if (settings.schema) {
      this._schema = new JSONSchemaBridge(
        settings.schema,
        createValidator(settings.schema)
      );
    }

    // Restore previously loaded project
    appRestored
      .then(() => this._state.fetch(StateID))
      .then(data => {
        this._setProject(data as any);

        if (this.project) {
          this.open(this.project.path);
        }
      })
      .catch(error => {
        console.error('Unable to restore saved project.', error);
        this.reset();
      });
  }

  /**
   * Name of the project configuration file
   */
  get configurationFilename(): string {
    return this._configurationFilename;
  }

  /**
   * Default path to open in a project
   */
  get defaultPath(): string {
    return this._defaultPath;
  }

  /**
   * Active project
   */
  get project(): Project.IModel | null {
    return this._project;
  }

  /**
   * Set the active project
   *
   * null = no active project
   *
   * @param newProject Project model
   */
  protected _setProject(newProject: Project.IModel | null): void {
    let changed = this._project !== newProject;
    if (!changed && !this._project && !newProject) {
      changed = !JSONExt.deepEqual(newProject as any, this._project as any);
    }

    if (changed) {
      this._project = newProject;
      this._state.save(StateID, this._project as any);
      this.projectChanged.emit(this._project);
    }
  }

  /**
   * A signal emitted when the project changes.
   */
  readonly projectChanged = new Signal<this, Project.IModel>(this);

  /**
   * Schema to be handled by the form
   */
  get schema(): JSONSchemaBridge | null {
    return this._schema;
  }

  /**
   * Generate a new project in path
   *
   * @param path Path where to generate the project
   * @param options Project template parameters
   */
  async create(
    path: string,
    options: ReadonlyJSONObject
  ): Promise<Project.IModel> {
    let endpoint = 'projects';
    if (path.length > 0) {
      endpoint = URLExt.join(endpoint, path);
    }

    const answer = await requestAPI<{ project: Project.IModel }>(endpoint, {
      method: 'POST',
      body: JSON.stringify(options)
    });

    this._setProject(answer.project);
    return this.project;
  }

  /**
   * Close the current project
   */
  async close(): Promise<void> {
    await this.open('');
  }

  /**
   * Delete the current project
   */
  async delete(): Promise<void> {
    let endpoint = 'projects';
    if (this.project.path.length > 0) {
      endpoint = URLExt.join(endpoint, this.project.path);
    }

    // Close the project before requesting its deletion
    await this.close();

    return requestAPI<void>(endpoint, {
      method: 'DELETE'
    });
  }

  /**
   * Open the folder path as the active project
   *
   * If path is empty, close the active project.
   *
   * @param path Project folder path
   * @returns The opened project model
   */
  async open(path: string): Promise<Project.IModel> {
    let endpoint = 'projects';
    if (path.length > 0) {
      endpoint = URLExt.join(endpoint, path);
    }

    const answer = await requestAPI<{ project: Project.IModel }>(endpoint, {
      method: 'GET'
    });

    this._setProject(answer.project);
    return this.project;
  }

  /**
   * Reset current state
   */
  reset(): void {
    this._setProject(null);
  }

  // Private attributes
  private _configurationFilename: string;
  private _defaultPath: string | null = null;
  private _project: Project.IModel | null = null;
  private _schema: JSONSchemaBridge | null = null;
  private _state: IStateDB;
}

/**
 * Reset the current application workspace:
 * - Save all opened files
 * - Close all opened files
 * - Go to the root path
 *
 * @param commands Commands registry
 */
async function resetWorkspace(commands: CommandRegistry): Promise<void> {
  await commands.execute(ForeignCommandIDs.saveAll);
  await commands.execute(ForeignCommandIDs.closeAll);

  await commands.execute(ForeignCommandIDs.goTo, {
    path: '/'
  });
}

/**
 * Activate the project manager plugin
 *
 * @param app The application object
 * @param state The application state handler
 * @param browserFactory The file browser factory
 * @param settings The project template settings
 * @param palette The command palette
 * @param launcher The application launcher
 * @param menu The application menu
 * @param statusbar The application status bar
 */
export function activateProjectManager(
  app: JupyterFrontEnd,
  state: IStateDB,
  browserFactory: IFileBrowserFactory,
  settings: Templates.IProject,
  palette: ICommandPalette,
  launcher: ILauncher | null,
  menu: IMainMenu | null,
  statusbar: IStatusBar | null
): IProjectManager {
  const { commands } = app;
  const category = 'Project';

  // Cannot blocking wait for the application otherwise this will bock the all application at launch time
  const manager = new ProjectManager(settings, state, app.restored);

  commands.addCommand(CommandIDs.newProject, {
    caption: 'Create a new project.',
    execute: async args => {
      const cwd: string =
        (args['cwd'] as string) || browserFactory.defaultBrowser.model.path;

      let params = {};
      if (manager.schema) {
        const userForm = await showForm({
          schema: manager.schema,
          title: 'Project Parameters'
        });
        if (!userForm.button.accept) {
          return;
        }
        params = userForm.value;
      }

      try {
        const model = await manager.create(cwd, params);

        commands.execute(CommandIDs.openProject, {
          path: model.path
        });
      } catch (error) {
        await manager.close();
        console.error('Fail to render the project', error);
        showErrorMessage('Fail to render the project', error);
      }
    },
    iconClass: args =>
      args['isPalette'] || !args['isLauncher']
        ? ''
        : 'jp-JupyterProjectProjectIcon',
    label: args => (!args['isLauncher'] ? 'New Project' : 'New')
  });

  commands.addCommand(CommandIDs.openProject, {
    label: args => (!args['isLauncher'] ? 'Open Project' : 'Open'),
    caption: 'Open a project',
    iconClass: args =>
      args['isLauncher'] ? 'jp-JupyterProjectIcon fa fa-folder-open fa-4x' : '',
    execute: async args => {
      // 1. Get the configuration file
      const path = args['path'] as string;
      let configurationFile: Contents.IModel;
      if (path) {
        // From commands arguments
        const filePath = PathExt.join(path, manager.configurationFilename);
        try {
          configurationFile = await app.serviceManager.contents.get(filePath, {
            content: false
          });
        } catch (reason) {
          console.error(reason);
          throw new Error(`Unable to get the configuration file ${filePath}.`);
        }
      } else {
        // From the user through an open file dialog
        const result = await FileDialog.getOpenFiles({
          filter: value => value.name === manager.configurationFilename,
          iconRegistry: browserFactory.defaultBrowser.model.iconRegistry,
          manager: browserFactory.defaultBrowser.model.manager,
          title: 'Select the project file'
        });

        if (result.button.accept) {
          configurationFile = result.value[0]; // Return the current directory if nothing is selected
        }
      }

      if (!configurationFile || configurationFile.type === 'directory') {
        return; // Bail early
      }

      // 2. Open the project
      try {
        await manager.open(PathExt.dirname(configurationFile.path));
      } catch (error) {
        console.error('Fail to open project', error);
        showErrorMessage('Fail to open project', error);
        return;
      }

      if (manager.defaultPath) {
        commands.execute(ForeignCommandIDs.openPath, {
          path: PathExt.join(manager.project.path, manager.defaultPath)
        });
      }
    }
  });

  commands.addCommand(CommandIDs.closeProject, {
    label: 'Close Project',
    caption: 'Close the current CoSApp project',
    isEnabled: () => manager.project !== null,
    execute: async () => {
      try {
        await resetWorkspace(commands);
        manager.close();
        // TODO Clean kernel white list
      } catch (error) {
        showErrorMessage('Failed to remove the current project', error);
      }
    }
  });

  commands.addCommand(CommandIDs.deleteProject, {
    label: 'Delete Project',
    caption: 'Delete a Project',
    isEnabled: () => manager.project !== null,
    execute: async () => {
      // TODO let environment = manager.project.environment;
      const userChoice = await showDialog({
        title: 'Delete',
        // eslint-disable-next-line prettier/prettier
        body: `Are you sure you want to permanently delete the project '${manager.project.name}' in ${manager.project.path}?`,
        buttons: [Dialog.cancelButton(), Dialog.warnButton({ label: 'DELETE' })]
      });
      if (!userChoice.button.accept) {
        return;
      }
      // 1. Remove asynchronously the folder
      resetWorkspace(commands);
      try {
        await manager.delete();
      } catch (error) {
        showErrorMessage('Failed to remove the project folder', error);
      }
      // TODO 2. Remove associated conda environment
      // try {
      //   if (environment) {
      //     manager.environmentManager.remove(environment);
      //   }
      // } catch (error) {
      //   showErrorMessage(
      //     `Failed to remove the project environment ${environment}`,
      //     error
      //   );
      // }
    }
  });

  if (launcher) {
    // Add Project Cards
    [CommandIDs.newProject, CommandIDs.openProject].forEach(command => {
      launcher.add({
        command,
        args: { isLauncher: true },
        category
      });
    });
  }

  const projectCommands = [
    CommandIDs.newProject,
    CommandIDs.openProject,
    CommandIDs.closeProject,
    CommandIDs.deleteProject
  ];

  if (menu) {
    const submenu = new Menu({ commands });
    submenu.title.label = 'Project';
    projectCommands.forEach(command => {
      submenu.addItem({
        command
      });
    });
    // Add `Project` entries as submenu of `File`
    menu.fileMenu.addGroup(
      [
        {
          submenu,
          type: 'submenu'
        },
        {
          type: 'separator'
        }
      ],
      0
    );
  }

  projectCommands.forEach(command => {
    palette.addItem({
      command,
      category,
      args: { isPalette: true }
    });
  });

  if (statusbar) {
    statusbar.registerStatusItem(`${PluginID}:project-status`, {
      align: 'left',
      item: createProjectStatus({ manager }),
      rank: -3
    });
  }

  return manager;
}
