# Super Review Agent v2.1 - 快速开始

> **3 分钟配置 + 开始使用文档自动审查和修复工具**

---

## 🎉 v2.1 新功能

**Codex 路径自动检测** - 无需手动指定 `--codex-cmd` 参数！

脚本会自动检测以下位置的 Codex CLI：
- PATH 环境变量中的 `codex` 命令
- Windows: `C:\Users\{用户名}\AppData\Roaming\npm\codex.cmd`
- Windows: `C:\Program Files\nodejs\codex.cmd`

如果自动检测失败，仍可手动指定：`--codex-cmd "路径"`

---

## ⚡ 快速配置（首次使用必须）

### 1. 设置环境变量

```bash
setx CLAUDE_CODE_GIT_BASH_PATH "D:\Program Files\Git\usr\bin\bash.exe"
```

### 2. 重启命令行

**关闭当前窗口 → 打开新窗口**（环境变量生效必须步骤）

### 3. 验证配置

```bash
cd d:\git\1108\AI_ad_spend02
echo %CLAUDE_CODE_GIT_BASH_PATH%
# 应输出: D:\Program Files\Git\usr\bin\bash.exe
```

---

## 🚀 运行测试

### 方法 A: 自动化测试（推荐）

```bash
cd test_super_review
run_full_test.bat
```

### 方法 B: 单独测试

```bash
# 测试 1: 单元测试
python test_parse_p0_p1.py

# 测试 2: Codex 审查（自动检测 Codex 路径）
python super_review_agent.py review-only ^
  --doc "docs\3.dev-guides\DDD_API_ARCHITECTURE_polished.md" ^
  --codex-prompt "test_super_review\reviewer_prompt.txt" ^
  --output "test_super_review\review_output.md" ^
  --verbose

# 测试 3: Codex 审查 + Claude 修复（自动检测 Codex 路径）
python super_review_agent.py fix-once ^
  --doc "docs\3.dev-guides\DDD_API_ARCHITECTURE_polished.md" ^
  --codex-prompt "test_super_review\reviewer_prompt.txt" ^
  --skill-name "doc-fixer-claude" ^
  --output "test_super_review\DDD_ARCH_fixed_once.md" ^
  --verbose
```

---

## 📚 文档索引

| 文档 | 用途 | 优先级 |
|------|------|--------|
| [SUPER_REVIEW_AGENT_FINAL_SUMMARY.md](SUPER_REVIEW_AGENT_FINAL_SUMMARY.md) | **完整开发报告** | ⭐⭐⭐ |
| [test_super_review/ENV_SETUP_GUIDE.md](test_super_review/ENV_SETUP_GUIDE.md) | **环境配置详细指南** | ⭐⭐⭐ |
| [SUPER_REVIEW_AGENT_USAGE.md](SUPER_REVIEW_AGENT_USAGE.md) | **完整使用手册** (320 行) | ⭐⭐ |
| [test_super_review/README.md](test_super_review/README.md) | 测试套件总览 | ⭐⭐ |
| [test_super_review/TEST_REPORT.md](test_super_review/TEST_REPORT.md) | 详细测试报告 | ⭐ |
| [test_super_review/TESTING_SUMMARY.md](test_super_review/TESTING_SUMMARY.md) | 测试总结 | ⭐ |

---

## 🎯 4 种运行模式

### 1. review-only - 只审查

```bash
python super_review_agent.py review-only \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" \
  --output tmp/review.md \
  --verbose
```

**用途**: 快速生成文档审查报告（P0/P1 缺陷列表）

---

### 2. fix-once - 审查 + 修复一次

```bash
python super_review_agent.py fix-once \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" \
  --skill-name "doc-fixer-claude" \
  --output tmp/fixed.md \
  --verbose
```

**用途**: 自动修复一次 P0/P1 缺陷

---

### 3. auto-polish-loop - 多轮磨光

```bash
python super_review_agent.py auto-polish-loop \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" \
  --skill-name "doc-fixer-claude" \
  --max-rounds 5 \
  --output tmp/polished.md \
  --verbose
```

**用途**: 循环（审查 → 修复），直到无 P0/P1 或达到最大轮数

---

### 4. quick-check - 快速检测

```bash
python super_review_agent.py quick-check \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" \
  --verbose
```

**用途**: 只检测是否存在 P0/P1（返回码 0 或 1）

---

## 🐛 常见问题

### Q1: 环境变量设置后仍然报错

**检查**:
1. ✅ 是否已重新打开命令行窗口？
2. ✅ 验证命令 `echo %CLAUDE_CODE_GIT_BASH_PATH%` 是否输出正确路径？

---

### Q2: Codex 命令未找到

**解决方案**: 使用完整路径
```bash
--codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd"
```

---

### Q3: 测试失败

**查看详细日志**:
```bash
# 添加 --verbose 参数
python super_review_agent.py review-only ... --verbose
```

---

## 📊 期望测试结果

### 成功标志

```
========================================================================
[SUCCESS] 所有测试通过!
========================================================================

生成的文件:
- test_super_review\review_output_batch.md  (review-only 输出)
- test_super_review\DDD_ARCH_fixed_once.md  (fix-once 输出)
```

### 文件验证

```bash
# 检查生成的文件
dir test_super_review\*.md
```

---

## 🔗 相关资源

- **源码**: [super_review_agent.py](super_review_agent.py)
- **完整报告**: [SUPER_REVIEW_AGENT_FINAL_SUMMARY.md](SUPER_REVIEW_AGENT_FINAL_SUMMARY.md)
- **环境配置**: [test_super_review/ENV_SETUP_GUIDE.md](test_super_review/ENV_SETUP_GUIDE.md)
- **使用手册**: [SUPER_REVIEW_AGENT_USAGE.md](SUPER_REVIEW_AGENT_USAGE.md)

---

**最后更新**: 2025-11-24 | **版本**: v2.0 | **基准**: SoT Freeze v1.0
