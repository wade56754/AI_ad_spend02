/**
 * Jest E2E 测试配置
 * 专门用于 Puppeteer E2E 测试
 */

module.exports = {
  preset: 'jest-puppeteer',
  testMatch: ['**/e2e/**/*.e2e.ts', '**/e2e/**/*.e2e.tsx'],
  testTimeout: 60000, // E2E 测试超时时间：60秒

  // 全局设置
  globalSetup: './e2e/setup/global-setup.ts',
  globalTeardown: './e2e/setup/global-teardown.ts',
  setupFilesAfterEnv: ['./e2e/setup/setup.ts'],

  // TypeScript 支持
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: {
        jsx: 'react',
        esModuleInterop: true,
        allowSyntheticDefaultImports: true,
      },
    }],
  },

  // 模块解析
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/../$1',
  },

  // 覆盖率配置（E2E 测试通常不收集代码覆盖率）
  collectCoverage: false,

  // 测试环境
  testEnvironment: 'node',

  // 详细输出
  verbose: true,
}
