import { ReactWidget, UseSignal } from '@jupyterlab/apputils';
import { TextItem } from '@jupyterlab/statusbar';
import { Widget } from '@lumino/widgets';
import * as React from 'react';
import { IProjectManager } from './tokens';

export interface IProjectStatusProps {
  manager: IProjectManager;
}

const ProjectComponent: React.FunctionComponent<IProjectStatusProps> = (
  props: IProjectStatusProps
) => {
  return (
    <UseSignal
      signal={props.manager.projectChanged}
      initialArgs={{ newValue: null, oldValue: null, type: 'open' }}
    >
      {(_, change): JSX.Element =>
        change.newValue ? (
          <TextItem
            source={change.newValue.name}
            title={`Active project: ${change.newValue.path}`}
          />
        ) : null
      }
    </UseSignal>
  );
};

export function createProjectStatus(props: IProjectStatusProps): Widget {
  return ReactWidget.create(<ProjectComponent {...props} />);
}
