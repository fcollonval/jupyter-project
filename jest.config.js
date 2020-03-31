module.exports = {
    // collectCoverageFrom: ['packages/*/src/*.{js,ts,tsx}'],
    // coverageReporters: ['html', 'lcovonly', 'text-summary'],
    moduleNameMapper: {
      '^uniforms-jlab$': '<rootDir>/packages/uniforms-jlab/src'
    },
    setupFiles: ['./scripts/setupEnzyme.js'],
    testMatch: ['**/__tests__/**/!(_)*.{js,ts,tsx}'],
    transform: {
      '^.+\\.(js|ts|tsx)$': './scripts/transform.js'
    }
  };