import { Dialog } from '@jupyterlab/apputils';
import { JSONObject } from '@phosphor/coreutils';

/**
 * Command IDs
 */
export namespace CommandIDs {
  export const newTemplateFile = 'jupyter-project:file-template';
}

/**
 * Form namespace
 */
export namespace Form {
  /**
   * Form widget interface
   */
  export interface IWidget extends Dialog.IBodyWidget<JSONObject> {
    /**
     * Submit the form
     *
     * Returns a promise that resolves if the form is valid otherwise
     * the promise is rejected.
     */
    submit: () => Promise<void>;
  }

  /**
   * Constructor options for forms
   */
  export interface IOptions {
    /**
     * JSON schema defining the forms
     */
    schema: any;
    /**
     * The top level text for the dialog.  Defaults to an empty string.
     */
    title: Dialog.Header;
    /**
     * Label for cancel button.
     */
    cancelLabel?: string;
    /**
     * The host element for the dialog. Defaults to `document.body`.
     */
    host?: HTMLElement;
    /**
     * Label for ok button.
     */
    okLabel?: string;
    /**
     * An optional renderer for dialog items.  Defaults to a shared
     * default renderer.
     */
    renderer?: Dialog.IRenderer;
  }
}

/**
 * Templates namespace
 */
export namespace Templates {
  /**
   * File template members
   */
  export interface IFile {
    /**
     * File template name
     */
    name: string;
    /**
     * Server endpoint to request
     */
    endpoint: string;
    /**
     * Destination folder of the template within the project directory
     */
    destination?: string;
    /**
     * JSON schema of the template parameters
     */
    schema?: JSONObject;
  }
  /**
   * Project template members
   */
  export interface IProject {
    /**
     * Project configuration file name
     */
    configurationFilename: string;
    /**
     * Default path to open when a project is created
     */
    defaultPath?: string;
    /**
     * JSON schema of the template parameter
     */
    schema?: JSONObject;
  }
  /**
   * Jupyter project settings
   */
  export interface ISettings {
    /**
     * List of defined file templates
     */
    fileTemplates: IFile[];
    /**
     * Project template configuration
     */
    projectTemplate: IProject | null;
  }
}
