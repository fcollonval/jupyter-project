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
import { PluginID, Templates, Project } from './tokens';

/**
 * Initialization data for the jupyter-project extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: PluginID,
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    browserFactory: IFileBrowserFactory,
    state: IStateDB,
    launcher: ILauncher | null,
    menu: IMainMenu | null,
    statusbar: IStatusBar | null
  ) => {
    const { commands } = app;

    const iconRegistry = defaultIconRegistry;
    registerIcons(iconRegistry);

    let manager: Project.IManager | null = null;

    requestAPI<Templates.ISettings>('settings', {
      method: 'GET'
    })
      .then(settings => {
        if (settings.projectTemplate) {
          manager = activateProjectManager(
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

        activateFileGenerator(
          commands,
          browserFactory,
          settings.fileTemplates,
          manager,
          palette,
          launcher,
          menu
        );

        console.log('JupyterLab extension jupyter-project is activated!');
      })
      .catch(error => {
        console.error(`Fail to activate ${PluginID}`, error);
      });
  },
  requires: [ICommandPalette, IFileBrowserFactory, IStateDB],
  optional: [ILauncher, IMainMenu, IStatusBar]
};

export default extension;
