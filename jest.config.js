module.exports = {
  // collectCoverageFrom: ['packages/*/src/*.{js,ts,tsx}'],
  // coverageReporters: ['html', 'lcovonly', 'text-summary'],
  setupFiles: ['./scripts/setupEnzyme.js'],
  testMatch: ['**/__tests__/**/!(_)*.{js,ts,tsx}'],
  transform: {
    '^.+\\.(js|ts|tsx)$': './scripts/transform.js'
  }
};
