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

/**
 * Simple regex validation for an SVG string taken from:
 * https://github.com/sindresorhus/is-svg
 *
 * MIT License
 *
 * Copyright (c) Sindre Sorhus <sindresorhus@gmail.com> (sindresorhus.com)
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
const regex = /^\s*(?:<\?xml[^>]*>\s*)?(?:<!doctype svg[^>]*\s*(?:\[?(?:\s*<![^>]*>\s*)*\]?)*[^>]*>\s*)?(?:<svg[^>]*>[^]*<\/svg>|<svg[^/>]*\/\s*>)\s*$/i;

export const isSvg = (input: string) =>
  Boolean(input) && regex.test(input.toString());
