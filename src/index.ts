import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './jupyter-project';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { ILauncher } from '@jupyterlab/launcher';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { ICommandPalette } from '@jupyterlab/apputils';
import { activateFileGenerator } from './filetemplates';
import { Templates } from './tokens';

/**
 * Initialization data for the jupyter-project extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'jupyter-project',
  autoStart: true,
  activate: async (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    browserFactory: IFileBrowserFactory,
    launcher: ILauncher | null,
    menu: IMainMenu | null
  ) => {
    console.log('JupyterLab extension jupyter-project is activated!');

    const { commands } = app;

    const settings = await requestAPI<Templates.ISettings>('settings', {
      method: 'GET'
    });

    await activateFileGenerator(
      commands,
      browserFactory,
      settings.fileTemplates,
      palette,
      launcher,
      menu
    );
  },
  requires: [ICommandPalette, IFileBrowserFactory],
  optional: [ILauncher, IMainMenu]
};

export default extension;
