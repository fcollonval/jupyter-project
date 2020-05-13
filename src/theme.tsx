import { createMuiTheme, Theme } from '@material-ui/core/styles';

function getCSSVar(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

export function getMuiTheme(): Theme {
  return createMuiTheme({
    palette: {
      primary: {
        main: getCSSVar('--jp-brand-color1'),
        contrastText: getCSSVar('--jp-ui-inverse-font-color1')
      },
      secondary: {
        main: getCSSVar('--jp-accent-color1'),
        contrastText: getCSSVar('--jp-ui-inverse-font-color1')
      },
      error: {
        main: getCSSVar('--jp-error-color1'),
        contrastText: getCSSVar('--jp-ui-inverse-font-color1')
      },
      warning: {
        main: getCSSVar('--jp-warn-color1'),
        contrastText: getCSSVar('--jp-ui-inverse-font-color1')
      },
      info: {
        main: getCSSVar('--jp-info-color1')
      },
      success: {
        main: getCSSVar('--jp-success-color1')
      },
      text: {
        primary: getCSSVar('--jp-ui-font-color1'),
        secondary: getCSSVar('--jp-ui-font-color2'),
        disabled: getCSSVar('--jp-ui-font-color3')
      },
      background: {
        default: getCSSVar('--jp-layout-color1'),
        paper: getCSSVar('--jp-layout-color2')
      }
    },
    typography: {
      fontFamily: getCSSVar('--jp-ui-font-family')
    }
  });
}
