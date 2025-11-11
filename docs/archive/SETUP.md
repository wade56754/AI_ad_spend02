# Supabase Starter 项目设置指南

## ✅ 已完成

- ✅ Supabase Starter 框架已下载
- ✅ API 客户端已集成到 `lib/api.ts`
- ✅ 环境变量示例已创建

## 🚀 快速配置

### 1. 创建环境变量文件

在 `with-supabase-app` 目录下创建 `.env.local`：

```env
NEXT_PUBLIC_SUPABASE_URL=https://jzmcoivxhiyidizncyaq.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6bWNvaXZ4aGl5aWRpem5jeWFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc4MTEsImV4cCI6MjA3Nzg5MzgxMX0.PIr4EdBjfyCgRa48IxK6yLS0yIER-_3qvd-Mv-4I7rw
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 2. 安装依赖（如果还没安装）

```bash
npm install
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 📋 下一步：添加业务页面

### 方式 1：从现有 frontend 目录复制

```bash
# 在项目根目录执行
cd E:\AI\ad-spend-system

# 复制页面
xcopy /E /I frontend\app\report with-supabase-app\app\report
xcopy /E /I frontend\app\finance with-supabase-app\app\finance
xcopy /E /I frontend\app\reconcile with-supabase-app\app\reconcile
```

### 方式 2：手动创建

参考 `../frontend/app/` 中的页面代码，在 `with-supabase-app/app/` 中创建对应页面。

## 🎨 使用 Starter 框架的优势

1. **认证系统**：已包含完整的登录、注册、密码重置功能
2. **UI 组件**：shadcn/ui 组件库已配置
3. **主题切换**：支持深色/浅色主题
4. **类型安全**：完整的 TypeScript 支持
5. **Supabase 集成**：客户端和服务器端都已配置好

## 📝 注意事项

1. **认证保护**：默认所有路由都需要登录，如需公开访问，修改 `middleware.ts`
2. **API 调用**：使用 `lib/api.ts` 中的函数调用 FastAPI 后端
3. **环境变量**：确保 `.env.local` 已正确配置

## 🔗 相关文档

- [Supabase Starter 集成指南](../INTEGRATION_GUIDE.md)
- [Bolt.new 使用指南](../BOLT_NEW_GUIDE.md)
- [API 文档](../API_DOCUMENTATION.md)


