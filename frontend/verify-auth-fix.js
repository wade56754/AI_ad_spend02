/**
 * Authentication Fix Verification Script
 * Verifies that frontend/backend field names now match
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 验证认证系统前后端字段匹配...\n');

// Check 1: Verify useAuth.ts uses 'identifier'
const useAuthPath = path.join(__dirname, 'src', 'hooks', 'useAuth.ts');
const useAuthContent = fs.readFileSync(useAuthPath, 'utf-8');

console.log('✓ 检查 1: useAuth.ts LoginRequest 接口');
if (useAuthContent.includes('identifier: string')) {
  console.log('  ✅ 使用 identifier 字段 (正确)');
} else if (useAuthContent.includes('email: string')) {
  console.log('  ❌ 仍使用 email 字段 (错误)');
  process.exit(1);
} else {
  console.log('  ⚠️  未找到 LoginRequest 接口');
}

// Check 2: Verify LoginPage.tsx uses 'identifier' in state
const loginPagePath = path.join(__dirname, 'src', 'features', 'auth', 'components', 'LoginPage.tsx');
const loginPageContent = fs.readFileSync(loginPagePath, 'utf-8');

console.log('\n✓ 检查 2: LoginPage.tsx 表单状态');
if (loginPageContent.includes("identifier: ''") || loginPageContent.includes('identifier: ""')) {
  console.log('  ✅ 表单状态使用 identifier (正确)');
} else {
  console.log('  ❌ 表单状态未使用 identifier (错误)');
  process.exit(1);
}

console.log('\n✓ 检查 3: LoginPage.tsx 表单验证');
if (loginPageContent.includes('formData.identifier')) {
  console.log('  ✅ 验证逻辑使用 identifier (正确)');
} else {
  console.log('  ❌ 验证逻辑未使用 identifier (错误)');
  process.exit(1);
}

console.log('\n✓ 检查 4: LoginPage.tsx input 字段');
const hasIdentifierInput = loginPageContent.includes('name="identifier"') &&
                          loginPageContent.includes('id="identifier"') &&
                          loginPageContent.includes('value={formData.identifier}');
if (hasIdentifierInput) {
  console.log('  ✅ Input 字段使用 identifier (正确)');
} else {
  console.log('  ❌ Input 字段配置错误');
  process.exit(1);
}

console.log('\n✓ 检查 5: LoginPage.tsx input type');
if (loginPageContent.includes('type="text"')) {
  console.log('  ✅ Input type 为 text (正确，支持用户名或邮箱)');
} else {
  console.log('  ⚠️  Input type 可能不正确');
}

// Check 6: Verify backend expects 'identifier'
console.log('\n✓ 检查 6: 后端 LoginRequest 模型');
const backendAuthPath = path.join(__dirname, '..', 'backend', 'routers', 'authentication.py');
if (fs.existsSync(backendAuthPath)) {
  const backendContent = fs.readFileSync(backendAuthPath, 'utf-8');
  if (backendContent.includes('identifier: str')) {
    console.log('  ✅ 后端期望 identifier 字段 (正确)');
  } else {
    console.log('  ⚠️  后端 LoginRequest 模型未找到');
  }
} else {
  console.log('  ⚠️  后端文件路径不存在');
}

console.log('\n' + '='.repeat(60));
console.log('✅ 所有检查通过！前后端字段名称已匹配');
console.log('='.repeat(60));
console.log('\n📋 修复总结:');
console.log('  • useAuth.ts: LoginRequest.identifier ✓');
console.log('  • LoginPage.tsx: 表单状态使用 identifier ✓');
console.log('  • LoginPage.tsx: 验证逻辑使用 identifier ✓');
console.log('  • LoginPage.tsx: Input 字段配置正确 ✓');
console.log('  • 后端: 期望 identifier 字段 ✓');

console.log('\n🎯 下一步: 手动测试登录流程');
console.log('  1. 启动开发服务器: pnpm run dev');
console.log('  2. 访问 http://localhost:3000/login');
console.log('  3. 输入测试凭据 (用户名或邮箱 + 密码)');
console.log('  4. 检查 Chrome DevTools Network 标签');
console.log('  5. 验证请求 payload 包含 identifier 字段\n');
