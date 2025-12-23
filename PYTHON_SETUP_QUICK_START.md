# Python 环境快速配置清单

> **适用于**: Windows 10/11  
> **Python 版本**: 3.11+  
> **预计时间**: 10-15 分钟

---

## ✅ 快速检查清单

- [ ] 1. 安装 Python 3.11+
- [ ] 2. 验证 Python 安装
- [ ] 3. 运行配置脚本
- [ ] 4. 测试代码工厂

---

## 🚀 快速安装步骤

### 步骤 1: 安装 Python（5分钟）

1. **下载**: https://www.python.org/downloads/
2. **运行安装程序**
3. **⚠️ 必须勾选**: "Add Python to PATH"
4. **点击**: "Install Now"

### 步骤 2: 验证安装（1分钟）

**打开新的命令提示符**（必须重新打开！）

```cmd
python --version
pip --version
```

**预期输出**：
```
Python 3.11.x
pip 23.x.x
```

### 步骤 3: 运行配置脚本（5分钟）

```cmd
cd D:\project\AI_ad_spend02
scripts\setup_python_env.bat
```

脚本会自动：
- ✅ 创建虚拟环境 (`.venv`)
- ✅ 升级 pip
- ✅ 安装项目依赖 (`requirements.txt`)
- ✅ 安装代码工厂依赖 (`agents/requirements.txt`)

### 步骤 4: 测试代码工厂（1分钟）

```cmd
.venv\Scripts\activate
python agents\skills\test_code_factory.py
```

**预期结果**：测试通过，无错误

---

## ⚠️ 常见问题快速修复

### 问题 1: `python --version` 报错

**解决**：
1. 重新打开命令提示符
2. 确认安装时勾选了 "Add Python to PATH"

### 问题 2: PowerShell 脚本被禁用

**解决**：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 3: 虚拟环境激活失败

**解决**：
```cmd
python -m venv .venv
scripts\setup_python_env.bat
```

---

## 📖 详细文档

遇到问题？查看详细指南：
- [完整配置指南](docs/PYTHON_ENV_SETUP.md)

---

**最后更新**: 2025-12-02



