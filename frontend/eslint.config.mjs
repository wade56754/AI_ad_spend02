// @ts-check
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactPlugin from 'eslint-plugin-react';
import reactHooksPlugin from 'eslint-plugin-react-hooks';
import nextPlugin from '@next/eslint-plugin-next';
import globals from 'globals';

export default tseslint.config(
  // 全局忽略
  {
    ignores: [
      '.next/**',
      'node_modules/**',
      'out/**',
      'coverage/**',
      '*.config.js',
      '*.config.mjs',
    ],
  },

  // 基础 ESLint 推荐规则
  eslint.configs.recommended,

  // TypeScript 推荐规则
  ...tseslint.configs.recommended,

  // React + Next.js 配置
  {
    files: ['**/*.{ts,tsx,js,jsx}'],
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooksPlugin,
      '@next/next': nextPlugin,
    },
    languageOptions: {
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        React: 'readonly',
      },
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      // === Next.js 规则 (等同于 next/core-web-vitals) ===
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs['core-web-vitals'].rules,

      // === React Hooks 规则 ===
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // === 关闭的规则 ===
      'react/no-unescaped-entities': 'off',
      '@next/next/no-page-custom-font': 'off',

      // === 禁止使用裸 HTML 标签 - 必须使用 shadcn/ui 组件 ===
      'react/forbid-elements': [
        'error',
        {
          forbid: [
            {
              element: 'button',
              message: "使用 <Button> 组件替代 <button> 标签 (from '@/components/ui/button')",
            },
            {
              element: 'input',
              message: "使用 <Input> 组件替代 <input> 标签 (from '@/components/ui/input')",
            },
            {
              element: 'select',
              message: "使用 <Select> 组件替代 <select> 标签 (from '@/components/ui/select')",
            },
            {
              element: 'textarea',
              message: "使用 <Textarea> 组件替代 <textarea> 标签 (from '@/components/ui/textarea')",
            },
            {
              element: 'label',
              message: "使用 <Label> 组件替代 <label> 标签 (from '@/components/ui/label')",
            },
          ],
        },
      ],

      // === TypeScript 规则 ===
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],

      // === 代码质量规则 ===
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'prefer-const': 'error',
      'no-var': 'error',
    },
  }
);
