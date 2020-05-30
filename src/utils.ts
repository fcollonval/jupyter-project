import { getProjectInfo } from './project';
import { Project } from './tokens';

/**
 * Namespace of foreign command IDs used
 */
export namespace ForeignCommandIDs {
  export const closeAll = 'application:close-all';
  export const documentOpen = 'docmanager:open';
  export const gitInit = 'git:init';
  export const goTo = 'filebrowser:go-to-path';
  export const openPath = 'filebrowser:open-path';
  export const saveAll = 'docmanager:save-all';
}

/**
 * Rendered a templated string with project info
 *
 * The template key must be {{ jproject.property }}. And
 * the properties available are those of Project.IInfo
 *
 * @param template Templated string
 * @param project Project information
 * @returns The rendered string
 */
export function renderStringTemplate(
  template: string,
  project: Project.IModel | null
): string {
  if (!project) {
    return template; // Bail early
  }
  const values = getProjectInfo(project);

  for (const key in values) {
    const regex = new RegExp(`{{\\s*jproject\\.${key}\\s*}}`, 'gi');
    const value = values[key as keyof typeof values];

    template = template.replace(regex, value);
  }

  return template;
}
