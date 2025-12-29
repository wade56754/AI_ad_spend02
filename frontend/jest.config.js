const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  // Setup files to run before each test
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],

  // Test environment
  testEnvironment: 'jest-environment-jsdom',

  // Module name mapper for path aliases
  moduleNameMapper: {
    '^@/features/(.*)$': '<rootDir>/src/features/$1',
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@/src/(.*)$': '<rootDir>/src/$1',
    '^@/components/(.*)$': '<rootDir>/src/components/$1',
    '^@/hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@/lib/(.*)$': '<rootDir>/src/lib/$1',
    '^@/modules/(.*)$': '<rootDir>/src/modules/$1',
    '^@/types/(.*)$': '<rootDir>/src/types/$1',
  },

  // Test match patterns
  testMatch: [
    '**/__tests__/**/*.(test|spec).[jt]s?(x)',
    '**/tests/**/*.(test|spec).[jt]s?(x)',
  ],

  // Ignore Playwright E2E tests (run separately with @playwright/test)
  testPathIgnorePatterns: [
    '/node_modules/',
    '/playwright/',
    '/e2e/',
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    'components/**/*.{js,jsx,ts,tsx}',
    'app/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
    '!**/coverage/**',
    '!**/tests/**',
  ],

  // Coverage thresholds (optional - can be adjusted)
  coverageThreshold: {
    global: {
      branches: 0,
      functions: 0,
      lines: 0,
      statements: 0,
    },
  },

  // Transform ignore patterns
  transformIgnorePatterns: [
    '/node_modules/',
    '^.+\\.module\\.(css|sass|scss)$',
  ],

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
