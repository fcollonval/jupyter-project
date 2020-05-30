import {
  ICommandPalette,
  InputDialog,
  showErrorMessage
} from '@jupyterlab/apputils';
import { URLExt } from '@jupyterlab/coreutils';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { ILauncher } from '@jupyterlab/launcher';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { Contents } from '@jupyterlab/services';
import {
  defaultIconRegistry,
  Icon,
  IconRegistry
} from '@jupyterlab/ui-components';
import { CommandRegistry } from '@phosphor/commands';
import { ReadonlyJSONObject } from '@phosphor/coreutils';
import { JSONSchemaBridge } from 'uniforms-bridge-json-schema';
import { showForm } from './form';
import { requestAPI } from './jupyter-project';
import { getProjectInfo } from './project';
import {
  CommandIDs,
  IProjectManager,
  PLUGIN_ID,
  Project,
  Templates
} from './tokens';
import { ForeignCommandIDs, renderStringTemplate } from './utils';
import { createValidator } from './validator';

/**
 * Generator of file from template
 */
class FileGenerator {
  /**
   * Constructor
   *
   * @param template File template description
   */
  constructor(template: Templates.IFile) {
    this._name = template.name;
    this._endpoint = template.endpoint;
    this._destination = template.destination;
    if (template.icon) {
      const icon: Icon.IModel = {
        name: `${PLUGIN_ID}-${this._endpoint}`,
        svg: template.icon
      };
      defaultIconRegistry.addIcon(icon);
      this._icon = IconRegistry.iconClassName(icon.name);
    }
    if (template.schema) {
      this._bridge = new JSONSchemaBridge(
        template.schema,
        createValidator(template.schema)
      );
    }
  }

  /**
   * Default destination within a project folder
   */
  get destination(): string | null {
    return this._destination;
  }

  /**
   * Server endpoint to request for generating the file.
   */
  get endpoint(): string {
    return decodeURIComponent(this._endpoint);
  }

  /**
   * Icon class name to display for this template
   */
  get icon(): string | null {
    return this._icon;
  }

  /**
   * User friendly template name
   */
  get name(): string {
    return decodeURIComponent(this._name);
  }

  /**
   * Schema to be handled by the form
   */
  get schema(): JSONSchemaBridge | null {
    return this._bridge;
  }

  /**
   * Generate a file from the template with the given parameters
   *
   * @param path Path in which the file should be rendered
   * @param params Template parameters
   * @param project Project context
   */
  async render(
    path: string,
    params: ReadonlyJSONObject,
    project: Project.IModel | null = null
  ): Promise<Contents.IModel> {
    let fullpath = path;
    if (project) {
      if (this.destination) {
        const destination = renderStringTemplate(this.destination, project);
        fullpath = URLExt.join(path, destination);
      }
      // Add the project properties to the user specified parameters
      params = {
        ...params,
        jproject: getProjectInfo(project)
      };
    }
    const endpoint = URLExt.join('files', this._endpoint, fullpath);
    return requestAPI<Contents.IModel>(endpoint, {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }

  private _bridge: JSONSchemaBridge | null = null;
  private _destination: string | null = null;
  private _endpoint: string;
  private _icon: string | null = null;
  private _name: string;
}

/**
 * Activate the file menu entries to generate new CoSApp files.
 *
 * Note: this is actually called at the end of the activation function for the project plugin
 *
 * @param commands Application commands registry
 * @param browserFactory File browser factory
 * @param manager Project manager
 * @param fileSettings File template parameters
 * @param palette Commands palette
 * @param menu Application menu
 * @param launcher Application launcher
 */
export function activateFileGenerator(
  commands: CommandRegistry,
  browserFactory: IFileBrowserFactory,
  fileSettings: Templates.IFile[],
  manager: IProjectManager | null,
  palette: ICommandPalette,
  launcher: ILauncher | null,
  menu: IMainMenu | null
): void {
  const paletteCategory = 'Text Editor';
  const launcherCategory = 'Templates';

  const generators = fileSettings.map(settings => new FileGenerator(settings));

  commands.addCommand(CommandIDs.newTemplateFile, {
    label: args => {
      let label = 'Template';
      if (args) {
        const isPalette = (args['isPalette'] as boolean) || false;
        const name = (args['name'] as string) || label;
        label = isPalette ? 'New Template' : name;
      }
      return label;
    },
    caption: args =>
      args['endpoint']
        ? `Create a new file from a template ${args['endpoint']}.`
        : 'Create a new file from a template.',
    iconClass: args =>
      args['isPalette']
        ? ''
        : (args['icon'] as string) || 'jp-JupyterProjectTemplateIcon',
    execute: async args => {
      // 1. Find the file generator
      let endpoint = args['endpoint'] as string;
      let generator: FileGenerator;
      if (!endpoint) {
        // Request the user to select a generator except if there is only one
        if (generators.length === 1) {
          generator = generators[0];
        } else {
          const results = await InputDialog.getItem({
            items: generators.map(generator => generator.name),
            title: 'Select a template'
          });

          if (!results.button.accept) {
            return;
          }

          generator = generators.find(
            generator => generator.name === results.value
          );
        }

        endpoint = generator.endpoint;
      } else {
        generator = generators.find(
          generator => generator.endpoint === endpoint
        );
      }

      // 2. Find where to generate the file
      let cwd: string;
      if (args['cwd'] && !args['isLauncher']) {
        // Launcher add automatically cwd to args - so we ignore that case
        // Use the argument path
        cwd = args['cwd'] as string;
      } else if (manager.project) {
        // Use the project path
        cwd = manager.project.path;
      } else {
        // Use the current path
        cwd = browserFactory.defaultBrowser.model.path;
      }

      // 3. Ask for parameters value
      let params = {};
      if (generator.schema) {
        const userForm = await showForm({
          schema: generator.schema,
          title: `Parameters of ${generator.name}`
        });
        if (!userForm.button.accept) {
          return;
        }
        params = userForm.value;
      }

      try {
        const model = await generator.render(cwd, params, manager.project);
        commands.execute(ForeignCommandIDs.documentOpen, {
          path: model.path
        });
      } catch (error) {
        console.error(`Fail to render ${generator.name}:\n${error}`);
        showErrorMessage(`Fail to render ${generator.name}`, error);
      }
    }
  });

  if (launcher) {
    generators.forEach(generator => {
      launcher.add({
        command: CommandIDs.newTemplateFile,
        category: launcherCategory,
        args: {
          isLauncher: true,
          name: generator.name,
          endpoint: generator.endpoint,
          icon: generator.icon
        }
      });
    });
  }

  if (menu) {
    // Add the templates to the File->New submenu
    const fileMenu = menu.fileMenu;
    fileMenu.newMenu.addGroup(
      generators.map(generator => {
        return {
          command: CommandIDs.newTemplateFile,
          args: {
            name: generator.name,
            endpoint: generator.endpoint,
            icon: generator.icon
          }
        };
      }),
      -1
    );
  }

  // Add the commands to the palette
  palette.addItem({
    command: CommandIDs.newTemplateFile,
    category: paletteCategory,
    args: { isPalette: true }
  });
}
