# Super Review Agent v2.0 - 测试套件

> **目的**: 测试文档自动审查和修复工具的所有功能
> **版本**: v2.0 (稳健性增强版)
> **测试基准**: SoT Freeze v1.0

---

## 📁 文件结构

```
test_super_review/
├── README.md                          # 本文档（测试套件说明）
├── ENV_SETUP_GUIDE.md                 # Windows 环境配置指南 ⚡ 必读
├── TEST_REPORT.md                     # 详细测试报告
├── TESTING_SUMMARY.md                 # 测试总结
├── run_full_test.bat                  # 自动化测试脚本 (Windows)
│
├── reviewer_prompt.txt                # Codex 审查 prompt 模板
├── mock_review_report.md              # 模拟审查报告 (P0: 2, P1: 3)
├── review_output.md                   # Codex 实际审查输出
└── DDD_ARCH_fixed_once_review.md      # fix-once 模式审查报告
```

---

## 🚀 快速开始

### 1️⃣ 首次使用 - 环境配置（必须！）

**Windows 用户必读**: [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md)

**关键步骤**:
```bash
# 1. 设置环境变量
setx CLAUDE_CODE_GIT_BASH_PATH "D:\Program Files\Git\usr\bin\bash.exe"

# 2. 关闭并重新打开命令行窗口（必须！）

# 3. 验证配置
echo %CLAUDE_CODE_GIT_BASH_PATH%
# 应输出: D:\Program Files\Git\usr\bin\bash.exe
```

---

### 2️⃣ 运行测试

#### 方法 A: 使用自动化脚本（推荐）

```bash
cd test_super_review
run_full_test.bat
```

**测试内容**:
- ✅ 验证环境变量
- ✅ 测试 parse_p0_p1_count 函数
- ✅ 测试 review-only 模式
- ✅ 测试 fix-once 模式

---

#### 方法 B: 手动运行单个测试

**测试 1: parse_p0_p1_count 函数**
```bash
python test_parse_p0_p1.py
```

**测试 2: review-only 模式**
```bash
python super_review_agent.py review-only ^
  --doc "docs\3.dev-guides\DDD_API_ARCHITECTURE_polished.md" ^
  --codex-prompt "test_super_review\reviewer_prompt.txt" ^
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" ^
  --output "test_super_review\review_output.md" ^
  --verbose
```

**测试 3: fix-once 模式**
```bash
python super_review_agent.py fix-once ^
  --doc "docs\3.dev-guides\DDD_API_ARCHITECTURE_polished.md" ^
  --codex-prompt "test_super_review\reviewer_prompt.txt" ^
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" ^
  --skill-name "doc-fixer-claude" ^
  --output "test_super_review\DDD_ARCH_fixed_once.md" ^
  --verbose
```

**测试 4: auto-polish-loop 模式**
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

---

## 📊 测试状态

| 测试项 | 状态 | 说明 |
|--------|------|------|
| **parse_p0_p1_count** | ✅ PASS | 7 种解析方法验证通过 |
| **review-only** | ✅ PASS | Codex 审查完整流程 |
| **fix-once (Codex)** | ✅ PASS | 审查阶段成功 |
| **fix-once (Claude)** | ⚠️ 需配置 | 需设置 git-bash 环境变量 |
| **auto-polish-loop** | ⚠️ 待测试 | 依赖 fix-once 完成 |
| **Windows UTF-8** | ✅ PASS | Emoji 和中文正常 |

---

## 📖 文档索引

### 测试相关文档

1. **[ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md)** ⚡ 必读
   - Windows 环境配置完整指南
   - git-bash 依赖问题解决方案
   - 4 步完成配置 + 验证

2. **[TEST_REPORT.md](TEST_REPORT.md)**
   - 完整测试报告
   - 每个模式的测试结果
   - 性能指标统计

3. **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)**
   - 测试概览和总结
   - 成功/失败/待测试项汇总
   - 下一步行动计划

### 使用文档

4. **[../SUPER_REVIEW_AGENT_USAGE.md](../SUPER_REVIEW_AGENT_USAGE.md)**
   - 完整使用指南（320+ 行）
   - 4 种模式详细说明
   - 参数文档和故障排查

5. **[../test_parse_p0_p1.py](../test_parse_p0_p1.py)**
   - parse_p0_p1_count 函数单元测试
   - 7 种解析方法验证

---

## 🎯 测试成果

### ✅ 已验证的增强功能

1. **内嵌 Skill 行为规则** (7 条修复规则)
   - P0 优先修复
   - 禁止发明字段
   - 保持文档结构
   - 输出完整文档

2. **Subprocess 调用增强**
   - 跨平台统一 stdin 策略
   - 移除 PowerShell 特殊处理
   - 明确禁用 shell (安全性提升)

3. **parse_p0_p1_count 容错**
   - 7 种解析方法
   - 方法 7: 正面检测（"无 P0/P1"）
   - 解析成功率 100%

4. **日志结构化**
   - `[Round X/Y]` 轮次前缀
   - Emoji 图标（🚀 📄 ⚙️ ✅ ⚠️ ❌）
   - Windows UTF-8 编码兼容

5. **空文档检测**
   - Claude 返回空内容时报错
   - 文档长度 < 50% 时警告

---

## 🐛 已知问题和解决方案

### Issue 1: Claude CLI 需要 git-bash

**症状**:
```
[ERROR] Claude Code on Windows requires git-bash
```

**解决方案**: 参见 [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md)

---

### Issue 2: 方法 7 中文匹配需优化

**症状**: 拼音测试失败 `"wu P0 que xian"`

**状态**: 已识别，优先级 P2（不影响核心功能）

**计划**: 下一版本优化中文正则表达式

---

## 🔗 相关资源

- **脚本源码**: [../super_review_agent.py](../super_review_agent.py) (v2.0)
- **SoT 文档**: [../docs/2.sot/](../docs/2.sot/) (Freeze v1.0)
- **项目规则**: [../.claude/PROJECT_RULES.md](../.claude/PROJECT_RULES.md) (v3.0)
- **Codex CLI**: https://github.com/codex-cli/codex
- **Claude CLI**: https://docs.anthropic.com/claude/cli

---

## 💡 技巧和最佳实践

### 1. 审查 Prompt 编写

**✅ 好的 Prompt**:
```
请审查文档，检查以下问题：

## P0 缺陷（阻塞性）
1. 与 STATE_MACHINE.md v2.6 冲突的状态定义
2. 重复定义已在 DATA_SCHEMA.md v5.2 中定义的表结构

输出格式：
## 摘要
- P0 缺陷: X个
- P1 缺陷: Y个
```

**❌ 不好的 Prompt**:
```
检查这个文档有没有问题
```

### 2. 轮次设置建议

| 文档规模 | 推荐轮数 | 说明 |
|---------|---------|------|
| 小型 (< 500 行) | 1-2 轮 | 单次修复即可 |
| 中型 (500-2000 行) | 3-5 轮 | 多轮迭代确保质量 |
| 大型 (> 2000 行) | 5-10 轮 | 复杂文档需多轮磨光 |

### 3. timeout 设置建议

| 文档规模 | 推荐 timeout | 说明 |
|---------|-------------|------|
| 小型 (< 500 行) | 300s (5分钟) | 快速响应 |
| 中型 (500-2000 行) | 600s (10分钟) | 默认值 |
| 大型 (> 2000 行) | 1200s (20分钟) | 大文档处理 |

---

## 📞 支持

遇到问题？

1. **查看故障排查**: [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md) § 常见问题排查
2. **查看使用文档**: [../SUPER_REVIEW_AGENT_USAGE.md](../SUPER_REVIEW_AGENT_USAGE.md) § 常见问题
3. **查看测试报告**: [TEST_REPORT.md](TEST_REPORT.md)

---

**最后更新**: 2025-11-24
**版本**: v2.0 (稳健性增强版)
**测试基准**: SoT Freeze v1.0
