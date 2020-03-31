import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './jupyter-project';

/**
 * Initialization data for the jupyter-project extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'jupyter-project',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension jupyter-project is activated!');

    requestAPI<any>('get_example')
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The jupyter_project server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default extension;
