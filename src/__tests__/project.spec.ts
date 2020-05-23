import 'jest';

jest.mock('@jupyterlab/services', () => {
  return {
    __esModule: true,
    ServerConnection: {
      makeRequest: jest.fn()
    }
  };
});

describe('jupyter-project/project', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('ProjectManager', () => {
    describe('constructor()', () => {
      it('should', () => {
        expect(1 + 2).toEqual(3);
      });
    });
  });
});
