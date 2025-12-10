/**
 * E2E 测试环境设置
 * 在每个测试文件运行前执行
 */

// 扩展 Jest 的超时时间
jest.setTimeout(60000)

// 全局变量声明
declare global {
  var BASE_URL: string
  var HEADLESS: boolean
}

// 设置全局变量
global.BASE_URL = process.env.BASE_URL || 'http://localhost:3000'
global.HEADLESS = process.env.HEADLESS !== 'false'

console.log('📋 E2E 测试环境配置:')
console.log(`   BASE_URL: ${global.BASE_URL}`)
console.log(`   HEADLESS: ${global.HEADLESS}`)
console.log(`   SLOWMO: ${process.env.SLOWMO || '0'}ms`)
console.log('')
