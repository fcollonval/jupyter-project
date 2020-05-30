import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ICommandPalette, IThemeManager } from '@jupyterlab/apputils';
import { IStateDB } from '@jupyterlab/coreutils';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { IGitExtension } from '@jupyterlab/git';
import { ILauncher } from '@jupyterlab/launcher';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { IStatusBar } from '@jupyterlab/statusbar';
import { defaultIconRegistry } from '@jupyterlab/ui-components';
import { IEnvironmentManager } from 'jupyterlab_conda';
import { activateFileGenerator } from './filetemplates';
import { requestAPI } from './jupyter-project';
import { activateProjectManager } from './project';
import { registerIcons } from './style';
import { setCurrentTheme } from './theme';
import { IProjectManager, PLUGIN_ID, Templates } from './tokens';

/**
 * Initialization data for the jupyter-project extension.
 */
const extension: JupyterFrontEndPlugin<IProjectManager> = {
  id: PLUGIN_ID,
  autoStart: true,
  activate: async (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    browserFactory: IFileBrowserFactory,
    state: IStateDB,
    launcher: ILauncher | null,
    menu: IMainMenu | null,
    statusbar: IStatusBar | null,
    themeManager: IThemeManager | null,
    condaManager: IEnvironmentManager | null,
    git: IGitExtension | null
  ): Promise<IProjectManager> => {
    const { commands } = app;

    const iconRegistry = defaultIconRegistry;
    registerIcons(iconRegistry);

    let manager: IProjectManager | null = null;

    try {
      const settings = await requestAPI<Templates.ISettings>('settings', {
        method: 'GET'
      });

      if (settings.projectTemplate) {
        manager = activateProjectManager(
          app,
          state,
          browserFactory,
          settings.projectTemplate,
          palette,
          condaManager,
          git,
          launcher,
          menu,
          statusbar
        );
      }

      if (settings.fileTemplates && settings.fileTemplates.length >= 0) {
        activateFileGenerator(
          commands,
          browserFactory,
          settings.fileTemplates,
          manager,
          palette,
          launcher,
          menu
        );
      }

      console.log('JupyterLab extension jupyter-project is activated!');
    } catch (error) {
      console.error(`Fail to activate ${PLUGIN_ID}`, error);
    }

    app.restored.then(() => {
      themeManager.themeChanged.connect((_, changedTheme) => {
        setCurrentTheme(changedTheme.newValue);
      });
      setCurrentTheme(themeManager.theme);
    });

    return manager;
  },
  requires: [ICommandPalette, IFileBrowserFactory, IStateDB],
  optional: [
    ILauncher,
    IMainMenu,
    IStatusBar,
    IThemeManager,
    IEnvironmentManager,
    IGitExtension
  ]
};

export default extension;
