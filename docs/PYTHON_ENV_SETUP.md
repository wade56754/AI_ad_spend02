# Python 环境配置指南

> **适用系统**: Windows 10/11  
> **Python 版本**: 3.11+  
> **最后更新**: 2025-12-02

---

## 📋 目录

1. [问题诊断](#1-问题诊断)
2. [解决方案](#2-解决方案)
3. [完整安装步骤](#3-完整安装步骤)
4. [验证安装](#4-验证安装)
5. [常见问题](#5-常见问题)

---

## 1. 问题诊断

### 症状

- 运行 `python --version` 提示未安装 Python
- Windows Store Python stub 存在但未激活
- 命令提示符中 Python 无法正常工作

### 原因

Windows 10/11 默认会在 PATH 中添加 Windows Store 的 Python stub（`python.exe`），这是一个重定向到 Microsoft Store 的占位符，并非真正的 Python 安装。

---

## 2. 解决方案

### 方案 A: 安装官方 Python（推荐）

**优点**：
- 完整功能，无限制
- 可以选择安装路径
- 更好的控制权

**步骤**：
1. 下载 Python 3.11+ 安装程序
2. 安装时**必须勾选** "Add Python to PATH"
3. 验证安装

### 方案 B: 使用 pyenv-win（高级用户）

**优点**：
- 可管理多个 Python 版本
- 避免 PATH 冲突

**适用场景**：
- 需要切换多个 Python 版本
- 开发多个项目

---

## 3. 完整安装步骤

### 步骤 1: 下载 Python

1. 访问 Python 官网：https://www.python.org/downloads/
2. 下载 Python 3.11 或更高版本（推荐 3.11 或 3.12）
3. 选择适合您系统的安装程序：
   - Windows x86-64: `python-3.11.x-amd64.exe`
   - Windows x86: `python-3.11.x.exe`

### 步骤 2: 安装 Python

1. **运行安装程序**

2. **重要配置选项**：
   - ✅ **勾选** "Add Python to PATH"（必须！）
   - ✅ 选择 "Install Now" 或自定义安装路径

   ![Python安装选项](https://docs.python.org/3/_images/win_installer.png)

3. **等待安装完成**

### 步骤 3: 禁用 Windows Store Python Stub（可选但推荐）

如果安装后仍然遇到问题，可以禁用 Windows Store 的 Python stub：

1. 打开 **设置** → **应用** → **应用和功能**
2. 搜索 "Python"
3. 如果看到 "Python 3.x (Windows Store)"，点击 → **卸载**

或者通过 PowerShell 禁用：

```powershell
# 以管理员身份运行 PowerShell
Get-AppxPackage *Python* | Remove-AppxPackage
```

### 步骤 4: 验证 Python 安装

**打开新的命令提示符或 PowerShell**（必须重新打开，环境变量才能生效）

```cmd
# CMD
python --version
pip --version

# PowerShell
python --version
pip --version
```

**预期输出**：
```
Python 3.11.x
pip 23.x.x from ... (python 3.11)
```

### 步骤 5: 运行配置脚本

**使用 CMD**：
```cmd
cd D:\project\AI_ad_spend02
scripts\setup_python_env.bat
```

**使用 PowerShell**：
```powershell
cd D:\project\AI_ad_spend02
.\scripts\setup_python_env.ps1
```

### 步骤 6: 激活虚拟环境并测试

**CMD**：
```cmd
.venv\Scripts\activate
python agents\skills\test_code_factory.py
```

**PowerShell**：
```powershell
.\.venv\Scripts\Activate.ps1
python agents\skills\test_code_factory.py
```

**注意**：如果 PowerShell 提示"无法加载脚本，因为在此系统上禁止运行脚本"，请运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 4. 验证安装

### 4.1 验证 Python 环境

```cmd
python --version          # 应显示 Python 3.11.x 或更高版本
pip --version             # 应显示 pip 版本
python -m pip --version   # 另一种验证方式
```

### 4.2 验证虚拟环境

```cmd
# 激活虚拟环境
.venv\Scripts\activate

# 验证虚拟环境中的 Python
python --version
where python              # 应指向 .venv\Scripts\python.exe

# 查看已安装的包
pip list
```

### 4.3 验证代码工厂

```cmd
# 在虚拟环境中运行测试
python agents\skills\test_code_factory.py
```

**预期输出**：测试通过，没有错误

---

## 5. 常见问题

### Q1: 安装 Python 后，`python --version` 仍然报错

**原因**：
- 环境变量未生效
- Windows Store Python stub 仍然在 PATH 前面

**解决方案**：
1. **重新打开命令提示符/PowerShell**（环境变量需要重启终端）
2. 检查 PATH 环境变量：
   ```cmd
   echo %PATH%
   ```
   确认 Python 安装路径（如 `C:\Python311` 或 `C:\Users\用户名\AppData\Local\Programs\Python\Python311`）在 PATH 中
3. 如果 Windows Store Python stub 仍然存在，按照步骤 3 禁用它

### Q2: PowerShell 提示"无法加载脚本"

**错误信息**：
```
无法加载文件 .\setup_python_env.ps1，因为在此系统上禁止运行脚本
```

**解决方案**：
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后重新运行脚本。

### Q3: 虚拟环境激活失败

**错误信息**：
```
'activate' 不是内部或外部命令
```

**原因**：
- 虚拟环境未正确创建
- 路径错误

**解决方案**：
1. 确认在项目根目录（`D:\project\AI_ad_spend02`）
2. 手动创建虚拟环境：
   ```cmd
   python -m venv .venv
   ```
3. 重新运行配置脚本

### Q4: pip 安装依赖失败

**可能原因**：
- 网络问题
- 依赖冲突
- Python 版本不兼容

**解决方案**：
1. 升级 pip：
   ```cmd
   python -m pip install --upgrade pip
   ```
2. 使用国内镜像（如果网络慢）：
   ```cmd
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
3. 检查 Python 版本（必须是 3.11+）

### Q5: 代码工厂测试失败

**检查清单**：
1. ✅ 虚拟环境已激活（命令提示符前应显示 `(.venv)`）
2. ✅ 已安装所有依赖：`pip install -r agents/requirements.txt`
3. ✅ Python 版本正确：`python --version`
4. ✅ 项目路径正确：`cd D:\project\AI_ad_spend02`

**调试步骤**：
```cmd
# 检查依赖是否安装
pip list | findstr pyyaml
pip list | findstr pydantic
pip list | findstr rich

# 手动测试导入
python -c "import yaml; import pydantic; import rich; print('OK')"
```

### Q6: 多个 Python 版本冲突

**症状**：
- 系统中有多个 Python 版本
- `python` 和 `python3` 指向不同版本

**解决方案**：
1. 使用完整路径：
   ```cmd
   C:\Python311\python.exe --version
   ```
2. 使用 pyenv-win 管理多个版本（高级）
3. 卸载不需要的版本，只保留一个

---

## 📚 相关文档

- [项目 README](../README.md)
- [快速开始指南](../QUICK_START.md)
- [开发指南](./3.dev-guides/BACKEND_SETUP.md)

---

## 🔗 参考资源

- [Python 官方文档](https://docs.python.org/3/)
- [pip 用户指南](https://pip.pypa.io/en/stable/user_guide/)
- [venv 虚拟环境](https://docs.python.org/3/library/venv.html)

---

**最后更新**: 2025-12-02  
**维护者**: 开发团队

