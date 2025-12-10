/**
 * 全局测试设置
 * 在所有 E2E 测试运行前执行一次
 */

import { spawn, ChildProcess } from 'child_process'
import { promisify } from 'util'
import path from 'path'

const sleep = promisify(setTimeout)

let devServer: ChildProcess | null = null

export default async function globalSetup() {
  console.log('\n🚀 启动前端开发服务器...\n')

  // 启动 Next.js 开发服务器
  devServer = spawn('npm', ['run', 'dev'], {
    cwd: path.join(__dirname, '../..'),
    stdio: 'pipe',
    shell: true,
  })

  // 监听输出，等待服务器就绪
  return new Promise<void>((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('开发服务器启动超时'))
    }, 60000) // 60秒超时

    devServer?.stdout?.on('data', (data) => {
      const output = data.toString()
      console.log('[Dev Server]', output)

      // 检测服务器是否就绪
      if (output.includes('Ready') || output.includes('Local:')) {
        clearTimeout(timeout)
        console.log('\n✅ 开发服务器已就绪\n')
        resolve()
      }
    })

    devServer?.stderr?.on('data', (data) => {
      console.error('[Dev Server Error]', data.toString())
    })

    devServer?.on('error', (error) => {
      clearTimeout(timeout)
      reject(error)
    })
  })
}

// 导出 devServer 以便 teardown 使用
export { devServer }
