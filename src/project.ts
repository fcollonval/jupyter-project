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
import { Signal, Slot } from '@phosphor/signaling';
import { Menu } from '@phosphor/widgets';
import { IEnvironmentManager, Conda } from 'jupyterlab_conda';
import { INotification } from 'jupyterlab_toastify';
import JSONSchemaBridge from 'uniforms-bridge-json-schema';
import YAML from 'yaml';
import { showForm } from './form';
import { requestAPI } from './jupyter-project';
import { createProjectStatus } from './statusbar';
import {
  CommandIDs,
  IProjectManager,
  PLUGIN_ID,
  Project,
  Templates
} from './tokens';
import { createValidator } from './validator';

/**
 * Default conda environment file
 */
const ENVIRONMENT_FILE = 'environment.yml';
/**
 * List of forbidden character in conda environment name
 */
const FORBIDDEN_ENV_CHAR = /[/\s:#]/gi;
/**
 * Project manager state ID
 */
const STATE_ID = `${PLUGIN_ID}:project`;

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
 * Namespace for Conda
 */
namespace CondaEnv {
  /**
   * Interface for conda environment file specification
   */
  export interface IEnvSpecs {
    /**
     * Channels to use
     */
    channels: string[];
    /**
     * Packages list
     */
    dependencies: string[];
    /**
     * Environment name
     */
    name: string;
    /**
     * Environment prefix
     */
    prefix: string;
  }
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

    if (settings.defaultCondaPackages) {
      this._defaultCondaPackages = settings.defaultCondaPackages;
    }

    if (settings.defaultPath) {
      this._defaultPath = settings.defaultPath;
    }

    this._editableInstall = settings.editableInstall;

    if (settings.schema) {
      this._schema = new JSONSchemaBridge(
        settings.schema,
        createValidator(settings.schema)
      );
    }

    // Restore previously loaded project
    appRestored
      .then(() => this._state.fetch(STATE_ID))
      .then(project => {
        this._setProject(project as any, 'open');

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
   * Default conda package to install in a new project - if no ENVIRONMENT_FILE found
   */
  get defaultCondaPackages(): string | null {
    return this._defaultCondaPackages;
  }

  /**
   * Default path to open in a project
   */
  get defaultPath(): string {
    return this._defaultPath;
  }

  /**
   * Should the project be installed in pip editable mode
   * in the conda environment?
   */
  get editableInstall(): boolean {
    return this._editableInstall;
  }

  /**
   * Active project
   */
  get project(): Project.IModel | null {
    return this._project;
  }

  /**
   * A signal emitted when the project changes.
   */
  get projectChanged(): Signal<this, Project.IChangedArgs> {
    return this._projectChanged;
  }

  /**
   * Schema to be handled by the form
   */
  get schema(): JSONSchemaBridge | null {
    return this._schema;
  }

  /**
   * Should we synchronize an conda environment with the project
   */
  get withConda(): boolean {
    return this.defaultCondaPackages ? true : false;
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

    this._setProject(answer.project, 'new');
    return this.project;
  }

  /**
   * Close the current project
   *
   * @param changeType Type of change; default 'open'
   */
  async close(changeType: Project.ChangeType = 'open'): Promise<void> {
    await this.open('', changeType);
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
    await this.close('delete');

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
   * @param changeType Type of change; default 'open'
   * @returns The opened project model
   */
  async open(
    path: string,
    changeType: Project.ChangeType = 'open'
  ): Promise<Project.IModel> {
    let endpoint = 'projects';
    if (path.length > 0) {
      endpoint = URLExt.join(endpoint, path);
    }

    const answer = await requestAPI<{ project: Project.IModel }>(endpoint, {
      method: 'GET'
    });

    this._setProject(answer.project, changeType);
    return this.project;
  }

  /**
   * Reset current state
   */
  reset(): void {
    this._setProject(null, 'open');
  }

  /**
   * Set the active project
   *
   * null = no active project
   *
   * @param newProject Project model
   * @param changeType Type of change
   */
  protected _setProject(
    newProject: Project.IModel | null,
    changeType: Project.ChangeType
  ): void {
    let changed = this._project !== newProject;
    if (!changed && !this._project && !newProject) {
      changed = !JSONExt.deepEqual(newProject as any, this._project as any);
    }

    if (changed) {
      const oldProject = { ...this._project };
      this._project = newProject;
      this._state.save(STATE_ID, this._project as any);
      this._projectChanged.emit({
        type: changeType,
        newValue: this._project,
        oldValue: oldProject
      });
    }
  }

  // Private attributes
  private _configurationFilename: string;
  private _defaultCondaPackages: string | null = null;
  private _defaultPath: string | null = null;
  private _editableInstall = true;
  private _project: Project.IModel | null = null;
  private _projectChanged = new Signal<this, Project.IChangedArgs>(this);
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
  condaManager: IEnvironmentManager | null,
  launcher: ILauncher | null,
  menu: IMainMenu | null,
  statusbar: IStatusBar | null
): IProjectManager {
  const { commands, serviceManager } = app;
  const category = 'Project';

  // Cannot blocking wait for the application otherwise this will bock
  // the all application at launch time
  const manager = new ProjectManager(settings, state, app.restored);

  // Update the conda environment description when closing a project
  // or if the associated environment changes.
  const condaSlot: Slot<Conda.IPackageManager, Conda.IPackageChange> = (
    _,
    change
  ) => {
    if (manager.project && change.environment === manager.project.environment) {
      Private.updateEnvironmentSpec(
        manager.project,
        condaManager,
        serviceManager.contents,
        commands
      ).catch(error => {
        console.error(
          `Fail to update environment '${change.environment} specifications.`,
          error
        );
      });
    }
  };
  if (condaManager) {
    manager.projectChanged.connect((_, change) => {
      if (
        change.type !== 'delete' &&
        change.oldValue &&
        change.oldValue.environment
      ) {
        Private.updateEnvironmentSpec(
          change.oldValue,
          condaManager,
          serviceManager.contents,
          commands
        ).catch(error => {
          console.error(
            `Fail to update environment '${change.oldValue.environment} specifications.`,
            error
          );
        });
      }
    });
  }

  commands.addCommand(CommandIDs.newProject, {
    caption: 'Create a new project.',
    execute: async args => {
      const cwd: string =
        (args['cwd'] as string) || browserFactory.defaultBrowser.model.path;
      let toastId = args['toastId'] as React.ReactText;
      const cleanToast = toastId === undefined;

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
        const message = 'Creating project.';
        if (toastId) {
          INotification.update({
            toastId,
            message
          });
        } else {
          toastId = await INotification.inProgress(message);
        }
        const model = await manager.create(cwd, params);

        await commands.execute(CommandIDs.openProject, {
          path: model.path,
          toastId
        });

        if (cleanToast) {
          INotification.update({
            toastId,
            message: `Project '${model.name}' successfully created.`,
            type: 'success',
            autoClose: 5000
          });
        }
      } catch (error) {
        const message = 'Fail to create the project';
        await manager.close();
        console.error(message, error);

        INotification.update({
          toastId,
          message,
          type: 'error'
        });
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
      let toastId = args['toastId'] as React.ReactText;
      const cleanToast = toastId === undefined;

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
        const message = 'Opening project...';
        if (toastId) {
          INotification.update({
            toastId,
            message
          });
        } else {
          toastId = await INotification.inProgress(message);
        }

        const model = await manager.open(
          PathExt.dirname(configurationFile.path)
        );

        if (manager.defaultPath) {
          await commands.execute(ForeignCommandIDs.openPath, {
            path: PathExt.join(model.path, manager.defaultPath)
          });
        }

        if (condaManager && manager.withConda) {
          condaManager.getPackageManager().packageChanged.disconnect(condaSlot);
          toastId = await Private.openProject(
            manager,
            serviceManager.contents,
            condaManager,
            commands,
            toastId
          );
          condaManager.getPackageManager().packageChanged.connect(condaSlot);

          // Force refreshing session to take into account the new environment
          serviceManager.sessions.refreshSpecs();
        }

        if (cleanToast) {
          if (toastId) {
            INotification.update({
              toastId,
              message: `Project '${model.name}' is ready.`,
              type: 'success',
              autoClose: 5000
            });
          }
        } else {
          if (toastId === null) {
            throw new Error('Fail to open conda environment');
          }
        }
      } catch (error) {
        const message = 'Fail to open project';
        console.error(message, error);

        INotification.update({
          toastId,
          message,
          type: 'error'
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
        if (condaManager) {
          condaManager.getPackageManager().packageChanged.disconnect(condaSlot);
        }
      } catch (error) {
        showErrorMessage('Failed to close the current project', error);
      }
    }
  });

  commands.addCommand(CommandIDs.deleteProject, {
    label: 'Delete Project',
    caption: 'Delete a Project',
    isEnabled: () => manager.project !== null,
    execute: async () => {
      const condaEnvironment = manager.project.environment;
      const projectName = manager.project.name;

      const userChoice = await showDialog({
        title: 'Delete',
        // eslint-disable-next-line prettier/prettier
        body: `Are you sure you want to permanently delete the project '${manager.project.name}' in ${manager.project.path}?`,
        buttons: [Dialog.cancelButton(), Dialog.warnButton({ label: 'DELETE' })]
      });
      if (!userChoice.button.accept) {
        return;
      }

      let toastId = await INotification.inProgress(
        `Removing project '${projectName}'...`
      );
      // 1. Remove asynchronously the folder
      await resetWorkspace(commands);
      try {
        await manager.delete();
      } catch (error) {
        const message = 'Failed to remove the project folder';
        console.error(message, error);
        INotification.update({ toastId, message, type: 'error' });
        toastId = null;
      }
      if (condaEnvironment && condaManager) {
        // 2. Remove associated conda environment
        const message = `Removing conda environment '${condaEnvironment}'...`;
        if (toastId) {
          INotification.update({ toastId, message });
        } else {
          toastId = await INotification.inProgress(message);
        }

        condaManager.getPackageManager().packageChanged.disconnect(condaSlot);
        try {
          await condaManager.remove(condaEnvironment);

          // Force refreshing session to take into account the new environment
          await serviceManager.sessions.refreshSpecs();
        } catch (error) {
          const message = `Failed to remove the project environment ${condaEnvironment}`;
          console.error(message, error);

          INotification.update({ toastId, message, type: 'error' });
          toastId = null;
        }
      }
      if (toastId) {
        INotification.update({
          toastId,
          message: `Project '${projectName}' removed.`,
          type: 'success',
          autoClose: 5000
        });
      }
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
    statusbar.registerStatusItem(`${PLUGIN_ID}:project-status`, {
      align: 'left',
      item: createProjectStatus({ manager }),
      rank: -3
    });
  }

  return manager;
}

/* eslint-disable no-inner-declarations */
namespace Private {
  /**
   * Open a project folder from its configuration file.
   * If no conda environment exists, creates one if requested.
   *
   * @param manager Project manager
   * @param contentService JupyterLab content service
   * @param conda Conda environment manager
   * @param toastId Toast ID to be updated with user information
   *
   * @returns The toast ID to be updated or null if it is dismissed
   */
  export async function openProject(
    manager: ProjectManager,
    contentService: Contents.IManager,
    conda: IEnvironmentManager,
    commands: CommandRegistry,
    toastId: React.ReactText
  ): Promise<React.ReactText | null> {
    const model = manager.project;
    let environmentName = (
      model.environment || model.name.replace(FORBIDDEN_ENV_CHAR, '_')
    ).toLocaleLowerCase();

    const foundEnvironment = (await conda.environments).find(
      value => value.name.toLocaleLowerCase() === environmentName
    );

    const { isIdentical, file, notInFile } = await Private.compareSpecification(
      conda,
      model,
      contentService
    );

    if (foundEnvironment) {
      environmentName = foundEnvironment.name;

      if (!isIdentical && file) {
        INotification.update({
          toastId,
          message: `Updating conda environment ${environmentName}... Please wait`
        });

        try {
          // 1. Remove package not in the environment specification file
          if (notInFile && notInFile.length > 0) {
            await conda
              .getPackageManager()
              .remove(notInFile, foundEnvironment.name);
          }
          // 2. Update the environment according to the file
          await conda.update(foundEnvironment.name, file, ENVIRONMENT_FILE);
        } catch (error) {
          const message = `Fail to update environment ${foundEnvironment.name}`;
          console.error(message, error);
          INotification.update({ toastId, message });
          toastId = null;
        }
      }
    } else {
      // Import an environment

      INotification.update({
        toastId,
        message: `Creating conda environment ${environmentName}... Please wait`
      });

      try {
        if (file) {
          // Create the environment from the requirements
          await conda.import(environmentName, file, ENVIRONMENT_FILE);
        } else {
          // Create an environment
          await conda.create(environmentName, manager.defaultCondaPackages);
          await updateEnvironmentSpec(
            { ...model, environment: environmentName },
            conda,
            contentService,
            commands
          );
        }
        if (manager.editableInstall) {
          await conda.getPackageManager(environmentName).develop(model.path);
        }
      } catch (error) {
        const message = `Fail to create the environment for ${model.name}`;
        console.error(message, error);
        INotification.update({ toastId, message });
        return null;
      }
    }

    // Communicate through the project environment change.
    if (model.environment !== environmentName) {
      const oldEnvironment = model.environment;
      model.environment = environmentName;
      manager.projectChanged.emit({
        type: 'open',
        oldValue: {
          ...model,
          environment: oldEnvironment
        },
        newValue: model
      });
    }

    // Update the config file
    const filePath = PathExt.join(model.path, manager.configurationFilename);
    await contentService.save(filePath, {
      type: 'file',
      format: 'text',
      content: JSON.stringify(model)
    });

    return toastId;
  }

  export async function updateEnvironmentSpec(
    project: Project.IModel | null,
    condaManager: IEnvironmentManager | null,
    contents: Contents.IManager,
    commands: CommandRegistry
  ): Promise<void> {
    if (project) {
      const { isIdentical, conda } = await compareSpecification(
        condaManager,
        project,
        contents
      );

      if (!isIdentical && conda) {
        const specPath = PathExt.join(project.path, ENVIRONMENT_FILE);
        await contents.save(specPath, {
          type: 'file',
          format: 'text',
          content: conda
        });

        INotification.info(
          `Environment '${project.environment}' specifications updated.`,
          {
            autoClose: 5000,
            buttons: [
              {
                label: 'Open file',
                callback: (): void => {
                  commands.execute(ForeignCommandIDs.openPath, {
                    path: specPath
                  });
                }
              }
            ]
          }
        );
      }
    }
  }

  const PACKAGE_NAME = /^([A-z][\w-]*)/;

  /**
   * Compare and returns the conda environment specifications from the conda
   * command and the environment file.
   *
   * @param condaManager Conda environment manager
   * @param project Active project
   * @param contents Content service
   * @returns [comparison, conda specification, file specification]
   */
  export async function compareSpecification(
    condaManager: IEnvironmentManager | null,
    project: Project.IModel | null,
    contents: Contents.IManager
  ): Promise<{
    isIdentical: boolean;
    conda?: string;
    file?: string;
    notInFile?: string[];
  }> {
    let conda: string;
    let condaPkgs: string[];
    if (condaManager && project && project.environment) {
      const description = await condaManager.export(project.environment, true);
      const specification = YAML.parse(
        await description.text()
      ) as CondaEnv.IEnvSpecs;
      condaPkgs = specification.dependencies
        .sort()
        .map(name => PACKAGE_NAME.exec(name)[0]);
      // Clean the specification from environment name and prefix
      delete specification.name;
      delete specification.prefix;
      conda = YAML.stringify(specification);
    }

    const specPath = PathExt.join(project.path, ENVIRONMENT_FILE);
    let file: string;
    let filePkgs: string[];
    try {
      const m = await contents.get(specPath, {
        content: true,
        format: 'text',
        type: 'file'
      });
      const specification = YAML.parse(m.content) as CondaEnv.IEnvSpecs;
      filePkgs = specification.dependencies
        .sort()
        .map(name => PACKAGE_NAME.exec(name)[0]);
      if (specification.name) {
        delete specification.name;
      }
      if (specification.prefix) {
        delete specification.prefix;
      }
      file = YAML.stringify(specification);
    } catch (error) {
      console.debug('No environment file', error);
    }

    const isIdentical = conda === file;
    let notInFile: string[];
    if (!isIdentical && condaPkgs) {
      if (filePkgs) {
        notInFile = new Array<string>();
        let fileI = 0;
        let filePkg = filePkgs[fileI];
        for (const condaPkg of condaPkgs) {
          if (condaPkg < filePkg) {
            notInFile.push(condaPkg);
          } else {
            while (condaPkg >= filePkg) {
              if (fileI < filePkgs.length - 1) {
                fileI += 1;
                filePkg = filePkgs[fileI];
              } else {
                notInFile.push(condaPkg);
                break;
              }
            }
          }
        }
      } else {
        notInFile = condaPkgs;
      }
    }

    return { isIdentical, conda, file, notInFile };
  }
}
/* eslint-enable no-inner-declarations */
