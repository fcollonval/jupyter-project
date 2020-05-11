import { IIconRegistry } from '@jupyterlab/ui-components';

// icon svg import statements
import projectSvg from '../style/icons/project.svg';
import templateSvg from '../style/icons/template.svg';
import { PluginID } from './tokens';

export function registerIcons(iconRegistry: IIconRegistry): void {
  iconRegistry.addIcon(
    {
      name: `${PluginID}-project`,
      svg: projectSvg
    },
    {
      name: `${PluginID}-template`,
      svg: templateSvg
    }
  );
}
