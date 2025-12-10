/**
 * 全局测试清理
 * 在所有 E2E 测试运行完成后执行一次
 */

export default async function globalTeardown() {
  console.log('\n🛑 关闭前端开发服务器...\n')

  // 由于无法直接访问 global-setup 中的 devServer
  // 我们通过进程名称查找并关闭
  if (process.platform === 'win32') {
    // Windows: 使用 taskkill
    const { exec } = require('child_process')
    exec('taskkill /F /IM node.exe /T', (error: any) => {
      if (error) {
        console.error('关闭服务器时出错:', error)
      } else {
        console.log('✅ 服务器已关闭')
      }
    })
  } else {
    // Unix/Linux/Mac: 使用 pkill
    const { exec } = require('child_process')
    exec('pkill -f "next dev"', (error: any) => {
      if (error) {
        console.error('关闭服务器时出错:', error)
      } else {
        console.log('✅ 服务器已关闭')
      }
    })
  }
}
