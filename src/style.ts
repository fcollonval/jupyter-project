import { IIconRegistry } from '@jupyterlab/ui-components';

// icon svg import statements
import projectSvg from '../style/icons/project.svg';
import templateSvg from '../style/icons/template.svg';
import { PLUGIN_ID } from './tokens';

export function registerIcons(iconRegistry: IIconRegistry): void {
  iconRegistry.addIcon(
    {
      name: `${PLUGIN_ID}-project`,
      svg: projectSvg
    },
    {
      name: `${PLUGIN_ID}-template`,
      svg: templateSvg
    }
  );
}
