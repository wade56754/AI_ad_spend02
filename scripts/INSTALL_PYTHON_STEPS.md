# Python 安装和环境变量配置步骤

> **适用于**: Windows 10/11  
> **预计时间**: 5-10 分钟

---

## 📥 方法 1: 使用安装程序（推荐）

### 步骤 1: 下载 Python

1. **访问 Python 官网**: https://www.python.org/downloads/
2. **点击下载按钮**，会自动下载最新版本的 Python
3. 或选择特定版本：
   - Python 3.11: https://www.python.org/downloads/release/python-3110/
   - Python 3.12: https://www.python.org/downloads/release/python-3120/

### 步骤 2: 运行安装程序

1. **双击下载的 `.exe` 文件**（例如 `python-3.11.0-amd64.exe`）

2. **重要配置**：
   - ✅ **必须勾选**: "Add Python to PATH"（位于安装界面底部）
   - 选择安装选项：
     - **Install Now**: 使用默认设置安装（推荐新手）
     - **Customize installation**: 自定义安装位置和组件（高级用户）

3. **点击 "Install Now"** 或 "Customize installation"

4. **等待安装完成**（通常需要 1-2 分钟）

### 步骤 3: 验证安装

**关闭当前所有命令提示符窗口，然后打开新的命令提示符**：

```cmd
python --version
pip --version
```

**预期输出**：
```
Python 3.11.x
pip 23.x.x from ... (python 3.11)
```

✅ **如果看到版本号，说明安装成功！**

---

## 🔧 方法 2: 手动配置环境变量（如果安装时未勾选 "Add Python to PATH"）

### 步骤 1: 找到 Python 安装路径

Python 通常安装在以下位置之一：
- `C:\Python311\`
- `C:\Python312\`
- `C:\Users\你的用户名\AppData\Local\Programs\Python\Python311\`
- `C:\Program Files\Python311\`

**确认方法**：
1. 打开文件资源管理器
2. 在地址栏输入 `%LOCALAPPDATA%\Programs\Python`
3. 查看是否有 Python 文件夹

### 步骤 2: 添加到系统 PATH

#### 方法 A: 使用图形界面

1. **右键 "此电脑"** → **属性**
2. 点击 **"高级系统设置"**
3. 点击 **"环境变量"** 按钮
4. 在 **"系统变量"** 区域，找到 `Path` 变量，点击 **"编辑"**
5. 点击 **"新建"**，添加以下路径（根据实际安装路径调整）：
   ```
   C:\Python311
   C:\Python311\Scripts
   ```
   或
   ```
   C:\Users\你的用户名\AppData\Local\Programs\Python\Python311
   C:\Users\你的用户名\AppData\Local\Programs\Python\Python311\Scripts
   ```
6. 点击 **"确定"** 保存所有更改

#### 方法 B: 使用 PowerShell 脚本（需要管理员权限）

1. **右键 PowerShell** → **"以管理员身份运行"**
2. 运行配置脚本：
   ```powershell
   cd D:\project\AI_ad_spend02
   .\scripts\install_python_guide.ps1
   ```
3. 脚本会自动检测 Python 并添加到 PATH

#### 方法 C: 使用命令行（需要管理员权限）

```cmd
# 以管理员身份运行 CMD

# 添加 Python 到 PATH（替换为实际路径）
setx /M PATH "%PATH%;C:\Python311;C:\Python311\Scripts"
```

**注意**: 使用 `/M` 参数需要管理员权限，这会修改系统级 PATH。

### 步骤 3: 验证配置

**重新打开命令提示符**（环境变量需要重启终端才能生效）：

```cmd
python --version
pip --version
```

---

## 🚀 方法 3: 使用 Chocolatey（高级用户）

如果您已安装 Chocolatey 包管理器：

```powershell
# 以管理员身份运行 PowerShell
choco install python311 --params '/InstallDir:C:\Python311'
```

Chocolatey 会自动配置环境变量。

---

## ✅ 安装完成后的下一步

安装并配置好 Python 后，运行项目配置脚本：

```cmd
cd D:\project\AI_ad_spend02
scripts\setup_python_env.bat
```

---

## ❓ 常见问题

### Q: 安装后 `python --version` 仍然报错

**原因**: 环境变量未生效

**解决**:
1. 确保**重新打开了命令提示符**（不是同一个窗口）
2. 检查 PATH 是否正确添加（使用 `echo %PATH%`）
3. 如果使用 `setx`，需要重启计算机或重新登录

### Q: 提示 "python 不是内部或外部命令"

**原因**: Python 未在 PATH 中

**解决**:
1. 确认 Python 已安装（检查安装目录是否存在）
2. 按照方法 2 手动添加到 PATH
3. 重新打开命令提示符

### Q: 安装时找不到 "Add Python to PATH" 选项

**原因**: 某些安装程序版本可能界面不同

**解决**:
1. 安装后使用方法 2 手动配置环境变量
2. 或使用 PowerShell 脚本自动配置

### Q: 有多个 Python 版本冲突

**解决**:
1. 卸载不需要的版本
2. 或使用 `py` 启动器：`py -3.11 --version`
3. 或使用虚拟环境隔离不同项目

---

## 📚 相关资源

- [Python 官方文档](https://docs.python.org/3/)
- [pip 用户指南](https://pip.pypa.io/en/stable/user_guide/)
- [项目快速开始指南](../PYTHON_SETUP_QUICK_START.md)

---

**最后更新**: 2025-12-02



