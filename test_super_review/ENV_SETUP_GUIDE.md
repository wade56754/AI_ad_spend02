# Super Review Agent - Windows 环境配置指南

> **目的**: 解决 Claude CLI 在 Windows 上需要 git-bash 的依赖问题
> **适用环境**: Windows 11/10
> **预计时间**: 3 分钟

---

## 🚨 问题现象

运行 `fix-once` 或 `auto-polish-loop` 模式时出现错误：

```
[ERROR] Claude Code on Windows requires git-bash
[ERROR] If installed but not in PATH, set environment variable pointing to your bash.exe
```

---

## ✅ 解决方案（4 步完成）

### 步骤 1: 查找 bash.exe 位置

打开命令行，运行：

```bash
where bash.exe
```

**典型输出**:
```
D:\Program Files\Git\usr\bin\bash.exe
C:\Program Files\Git\bin\bash.exe
C:\Windows\System32\bash.exe
```

**选择第一个路径**（通常是 Git 自带的 bash）

---

### 步骤 2: 设置永久环境变量

在**当前命令行窗口**运行（注意替换路径）：

```bash
setx CLAUDE_CODE_GIT_BASH_PATH "D:\Program Files\Git\usr\bin\bash.exe"
```

**成功提示**:
```
成功: 指定的值已得到保存。
```

⚠️ **注意**: 如果你的 Git 安装在其他位置（如 `C:\Program Files\Git`），请相应修改路径。

---

### 步骤 3: 重新打开命令行窗口 ⚡ 重要！

**环境变量只在新的命令行会话中生效！**

1. 关闭当前命令行窗口
2. 重新打开一个新的命令行窗口
3. 进入项目目录：
   ```bash
   cd d:\git\1108\AI_ad_spend02
   ```

---

### 步骤 4: 验证配置

在**新的命令行窗口**中运行：

```bash
echo %CLAUDE_CODE_GIT_BASH_PATH%
```

**期望输出**:
```
D:\Program Files\Git\usr\bin\bash.exe
```

**如果输出 `%CLAUDE_CODE_GIT_BASH_PATH%`（原样返回）**:
- ❌ 说明环境变量未生效
- ✅ 请确认已关闭并重新打开命令行窗口

---

## 🧪 测试验证

### 方法 A: 手动测试 fix-once 模式

```bash
python super_review_agent.py fix-once ^
  --doc "docs\3.dev-guides\DDD_API_ARCHITECTURE_polished.md" ^
  --codex-prompt "test_super_review\reviewer_prompt.txt" ^
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" ^
  --skill-name "doc-fixer-claude" ^
  --output "test_super_review\DDD_ARCH_fixed_once.md" ^
  --verbose
```

**成功标志**:
- ✅ `[1/2] 正在调用 Codex 进行审查...` → 成功
- ✅ `[2/2] 正在调用 Claude 进行修复...` → 成功
- ✅ 生成文件: `test_super_review\DDD_ARCH_fixed_once.md`

---

### 方法 B: 使用自动化测试脚本（推荐）

```bash
cd test_super_review
run_full_test.bat
```

**测试内容**:
1. 验证环境变量
2. 测试 `parse_p0_p1_count` 函数
3. 测试 `review-only` 模式
4. 测试 `fix-once` 模式

**成功提示**:
```
========================================================================
[SUCCESS] 所有测试通过!
========================================================================
```

---

## 🐛 常见问题排查

### Q1: `setx` 命令提示"访问被拒绝"

**原因**: 需要管理员权限

**解决方案**: 右键点击"命令提示符" → "以管理员身份运行"，然后重新执行 `setx` 命令

---

### Q2: 环境变量设置后仍然报错

**检查清单**:
1. ✅ 是否已关闭并重新打开命令行窗口？
2. ✅ 验证命令 `echo %CLAUDE_CODE_GIT_BASH_PATH%` 是否输出正确路径？
3. ✅ bash.exe 路径是否真实存在？运行 `dir "D:\Program Files\Git\usr\bin\bash.exe"` 验证

---

### Q3: Git 安装在 C 盘，但环境变量设置的是 D 盘

**解决方案**: 重新运行 `setx` 命令，使用正确的路径

```bash
# 示例：如果 Git 在 C:\Program Files\Git
setx CLAUDE_CODE_GIT_BASH_PATH "C:\Program Files\Git\usr\bin\bash.exe"
```

---

### Q4: 想要临时测试，不想设置永久环境变量

**临时方案**（仅当前会话有效）:

```bash
set CLAUDE_CODE_GIT_BASH_PATH=D:\Program Files\Git\usr\bin\bash.exe

# 然后立即运行测试（不要关闭窗口）
python super_review_agent.py fix-once ...
```

---

## 📊 配置前后对比

| 阶段 | review-only | fix-once | auto-polish-loop |
|------|------------|----------|------------------|
| **配置前** | ✅ 正常 | ❌ 失败 | ❌ 失败 |
| **配置后** | ✅ 正常 | ✅ 正常 | ✅ 正常 |

---

## 🎯 下一步

配置完成后，可以：

1. **运行完整测试套件**:
   ```bash
   cd test_super_review
   run_full_test.bat
   ```

2. **测试 auto-polish-loop 模式**（多轮磨光）:
   ```bash
   python super_review_agent.py auto-polish-loop ^
     --doc "docs\3.dev-guides\DDD_API_ARCHITECTURE_polished.md" ^
     --codex-prompt "test_super_review\reviewer_prompt.txt" ^
     --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" ^
     --skill-name "doc-fixer-claude" ^
     --max-rounds 3 ^
     --output "test_super_review\DDD_ARCH_polished.md" ^
     --verbose
   ```

3. **查看详细文档**:
   - [SUPER_REVIEW_AGENT_USAGE.md](../SUPER_REVIEW_AGENT_USAGE.md) - 完整使用指南
   - [TEST_REPORT.md](TEST_REPORT.md) - 测试报告
   - [TESTING_SUMMARY.md](TESTING_SUMMARY.md) - 测试总结

---

**最后更新**: 2025-11-24
**版本**: v2.0
**测试基准**: SoT Freeze v1.0
