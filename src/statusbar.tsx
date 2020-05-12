import { ReactWidget, UseSignal } from '@jupyterlab/apputils';
import { TextItem } from '@jupyterlab/statusbar';
import { Widget } from '@phosphor/widgets';
import * as React from 'react';
import { IProjectManager } from './tokens';

export interface IProjectStatusProps {
  manager: IProjectManager;
}

const ProjectComponent: React.FunctionComponent<IProjectStatusProps> = (
  props: IProjectStatusProps
) => {
  return (
    <UseSignal signal={props.manager.projectChanged}>
      {(_, project): JSX.Element =>
        project ? (
          <TextItem
            source={project.name}
            title={`Active project: ${project.path}`}
          />
        ) : null
      }
    </UseSignal>
  );
};

export function createProjectStatus(props: IProjectStatusProps): Widget {
  return ReactWidget.create(<ProjectComponent {...props} />);
}
