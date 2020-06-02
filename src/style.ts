import { LabIcon } from '@jupyterlab/ui-components';

// icon svg import statements
import projectSvg from '../style/icons/project.svg';
import templateSvg from '../style/icons/template.svg';
import { PLUGIN_ID } from './tokens';

export const projectIcon = new LabIcon({
  name: `${PLUGIN_ID}-project`,
  svgstr: projectSvg
});

export const templateIcon = new LabIcon({
  name: `${PLUGIN_ID}-template`,
  svgstr: templateSvg
});
