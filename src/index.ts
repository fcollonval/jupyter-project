import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { IStateDB } from '@jupyterlab/coreutils';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { ILauncher } from '@jupyterlab/launcher';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { IStatusBar } from '@jupyterlab/statusbar';
import { defaultIconRegistry } from '@jupyterlab/ui-components';
import { activateFileGenerator } from './filetemplates';
import { requestAPI } from './jupyter-project';
import { activateProjectManager } from './project';
import { registerIcons } from './style';
import { PluginID, Templates } from './tokens';

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
    menu: IMainMenu | null,
    statusbar: IStatusBar | null
  ) => {
    console.log('JupyterLab extension jupyter-project is activated!');

    const { commands } = app;

    const iconRegistry = defaultIconRegistry;
    registerIcons(iconRegistry);

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
        menu,
        statusbar
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
  optional: [ILauncher, IMainMenu, IStatusBar]
};

export default extension;
