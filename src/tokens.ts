import { Dialog } from '@jupyterlab/apputils';
import { JSONObject, Token } from '@phosphor/coreutils';
import { Signal } from '@phosphor/signaling';
import { Bridge } from 'uniforms';

/**
 * Plugin ID
 */
export const PluginID = 'jupyter-project';

/**
 * Project Manager Plugin Token
 */
export const IProjectManager = new Token<IProjectManager>(
  `${PluginID}:IProjectManager`
);

/**
 * Command IDs
 */
export namespace CommandIDs {
  /**
   * Close current project command
   */
  export const closeProject = 'jupyter-project:project-close';
  /**
   * Delete current project command
   */
  export const deleteProject = 'jupyter-project:project-delete';
  /**
   * Create new project command
   */
  export const newProject = 'jupyter-project:project-create';
  /**
   * Open project command
   */
  export const openProject = 'jupyter-project:project-open';
  /**
   * Create new file from template command
   */
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
     * uniforms.Bridge schema defining the forms
     */
    schema: Bridge;
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

export namespace Project {
  export interface IModel {
    /** Project name */
    name: string;
    /** Current project path */
    path: string;
  }
}
export interface IProjectManager {
  /** Current project properties */
  project: Project.IModel | null;
  /** Signal emitted when project changes */
  projectChanged: Signal<IProjectManager, Project.IModel>;
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
     * Icon to display for this template
     */
    icon?: string;
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
