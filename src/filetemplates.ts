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
import { CommandRegistry } from '@phosphor/commands';
import Ajv from 'ajv';
import { JSONSchemaBridge } from 'uniforms-bridge-json-schema';
import { requestAPI } from './jupyter-project';
import { CommandIDs, Templates } from './tokens';
import { Form } from './form';

const ajv = new Ajv({ allErrors: true, useDefaults: true });

function createValidator(schema: boolean | object): (model: object) => void {
  const validator = ajv.compile(schema);

  return (model: object): void => {
    validator(model);

    if (validator.errors && validator.errors.length) {
      throw { details: validator.errors };
    }
  };
}

class FileGenerator {
  constructor(templates: Templates.IFile) {
    this._name = templates.name;
    this._endpoint = templates.endpoint;
    this._destination = templates.destination;
    if (templates.schema) {
      this._bridge = new JSONSchemaBridge(
        templates.schema,
        createValidator(templates.schema)
      );
    }
  }

  get schema(): JSONSchemaBridge | null {
    return this._bridge;
  }

  get endpoint(): string {
    return decodeURIComponent(this._endpoint);
  }

  get name(): string {
    return this._name;
  }

  async render(
    path: string,
    params: any,
    inProject = false
  ): Promise<Contents.IModel> {
    let fullpath = path;
    if (inProject && this._destination) {
      fullpath = URLExt.join(path, this._destination);
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
  private _name: string;
}

/**
 * Activate the file menu entries to generate new CoSApp files.
 *
 * Note: this is actually called at the end of the activation function for the project plugin
 *
 * @param app
 * @param manager
 * @param palette
 * @param menu
 * @param launcher
 */
export async function activateFileGenerator(
  commands: CommandRegistry,
  browserFactory: IFileBrowserFactory,
  //   manager: Project.IModel,
  fileSettings: Templates.IFile[],
  palette: ICommandPalette,
  launcher: ILauncher | null,
  menu: IMainMenu | null
): Promise<void> {
  if (fileSettings.length === 0) {
    return; // Bail early
  }

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
    iconClass: (
      args // TODO add icon to settings
    ) =>
      args['isPalette']
        ? ''
        : args['isLauncher']
        ? 'fa fa-cogs fa-4x'
        : 'fa fa-cogs',
    execute: async args => {
      const cwd: string =
        (args['cwd'] as string) || browserFactory.defaultBrowser.model.path; // TODO or project folder

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
      }

      let params = {};
      if (generator.schema) {
        const userForm = await new Form(generator.schema).launch();
        if (!userForm.button.accept) {
          return;
        }
        params = userForm.value;
      }

      // if (isProject) TODO
      try {
        const model = await generator.render(cwd, params);
        commands.execute('docmanager:open', {
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
          endpoint: generator.endpoint
          // TODO icon: generator.icon
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
          args: { name: generator.name, endpoint: generator.endpoint }
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
