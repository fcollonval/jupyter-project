/**
 * Command IDs
 */
export namespace CommandIDs {
  export const newTemplateFile = 'jupyter-project:file-template';
}

export namespace Templates {
  export interface IFile {
    name: string;
    /**
     * Server endpoint to request
     */
    endpoint: string;
    destination?: string;
    schema?: object;
  }
  export interface IProject {
    configurationFilename: string;
    defaultPath?: string;
    schema?: object;
  }

  export interface ISettings {
    fileTemplates: IFile[];
    projectTemplate: IProject;
  }
}
