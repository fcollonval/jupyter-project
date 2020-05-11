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
import { Templates, PluginID } from './tokens';
import { IStateDB } from '@jupyterlab/coreutils';
import { activateProjectManager } from './project';

/**
 * Initialization data for the jupyter-project extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: PluginID,
  autoStart: true,
  activate: async (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    browserFactory: IFileBrowserFactory,
    state: IStateDB,
    launcher: ILauncher | null,
    menu: IMainMenu | null
  ) => {
    console.log('JupyterLab extension jupyter-project is activated!');

    const { commands } = app;

    const settings = await requestAPI<Templates.ISettings>('settings', {
      method: 'GET'
    });

    let manager = null;

    if (settings.projectTemplate) {
      manager = await activateProjectManager(
        app,
        state,
        browserFactory,
        settings.projectTemplate,
        palette,
        launcher,
        menu
      );
    }

    await activateFileGenerator(
      commands,
      browserFactory,
      settings.fileTemplates,
      manager,
      palette,
      launcher,
      menu
    );
  },
  requires: [ICommandPalette, IFileBrowserFactory, IStateDB],
  optional: [ILauncher, IMainMenu]
};

export default extension;
