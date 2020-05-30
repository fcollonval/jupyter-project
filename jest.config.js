const jestJupyterLab = require('@jupyterlab/testutils/lib/jest-config');

const jlabConfig = jestJupyterLab('jupyter-project', __dirname);

const {
  coverageDirectory,
  moduleFileExtensions,
  moduleNameMapper,
  preset,
  setupFilesAfterEnv,
  setupFiles,
  testPathIgnorePatterns
} = jlabConfig;

module.exports = {
  coverageDirectory,
  moduleFileExtensions,
  moduleNameMapper,
  preset,
  setupFilesAfterEnv,
  setupFiles,
  testPathIgnorePatterns,
  automock: false,
  collectCoverageFrom: ['src/**.{ts,tsx}', '!src/*.d.ts'],
  coverageReporters: ['lcov', 'text'],
  globals: {
      'ts-jest': {
          tsConfig: `./tsconfig.json`
      }
  },
  reporters: ['default'],
  testRegex: 'src/.*/.*.spec.ts[x]?$',
  transformIgnorePatterns: ['/node_modules/(?!(@jupyterlab/.*)/)']
};
