import 'jest';
import { renderStringTemplate } from '../utils';
import { Project } from '../tokens';

describe('jupyter-project/utils', () => {
  describe('renderStringTemplate', () => {
    it('should render a templated string with project', () => {
      // Given
      const project: Project.IModel = {
        name: 'banana',
        path: '/path/to/project'
      };
      // When
      const template =
        'dummy_{{jproject.namE }}_{{  jproject.path}}_{{jproject.name}}';
      const final = renderStringTemplate(template, project);

      // Then
      expect(final).toEqual('dummy_banana_/path/to/project_banana');
    });
  });
  it('should not change a string without template', () => {
    // Given
    const project: Project.IModel = {
      name: 'banana',
      path: '/path/to/project'
    };
    // When
    const template = 'dummy_template';
    const final = renderStringTemplate(template, project);

    // Then
    expect(final).toEqual(template);
  });
  it('should return the templated string if no project is provided', () => {
    // Given
    const project: Project.IModel | null = null;
    // When
    const template =
      'dummy_{{jproject.namE }}_{{  jproject.path}}_{{jproject.name}}';
    const final = renderStringTemplate(template, project);

    // Then
    expect(final).toEqual(template);
  });
});
