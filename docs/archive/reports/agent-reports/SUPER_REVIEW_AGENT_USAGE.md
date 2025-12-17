# Super Review Agent v2.0 - 使用指南

> **版本**: v2.0 (稳健性增强版)
> **发布日期**: 2025-11-24
> **适用环境**: Windows/macOS/Linux + Codex CLI + Claude CLI

---

## 📌 快速开始

### 前置条件

1. **Python 3.8+** 已安装
2. **Codex CLI** 已安装并在 PATH 中
   ```bash
   # 验证安装
   codex --version
   # 输出: codex-cli 0.63.0
   ```

3. **Claude CLI** 已安装并在 PATH 中（仅 fix-once 和 auto-polish-loop 模式需要）
   ```bash
   # 验证安装
   claude --version
   ```

---

## 🚀 四种运行模式

### 1. review-only: 只审查，不修复

**用途**: 快速生成文档审查报告，人工查看 P0/P1 缺陷

**命令**:
```bash
python super_review_agent.py review-only \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --output tmp/review.md \
  --verbose
```

**输出**:
- `tmp/review.md` - 完整审查报告（包含 P0/P1 缺陷列表）

**适用场景**:
- 初次审查文档
- 定期文档质量检查
- CI/CD 管道中的质量门禁

---

### 2. fix-once: 审查 + 修复一次

**用途**: 自动修复一次 P0/P1 缺陷，适合单次快速修复

**命令**:
```bash
python super_review_agent.py fix-once \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --skill-name doc-fixer-claude \
  --output tmp/fixed.md \
  --verbose
```

**输出**:
- `tmp/fixed_review.md` - 审查报告
- `tmp/fixed.md` - 修复后的文档

**适用场景**:
- 文档有少量已知问题
- 需要快速修复并验证

---

### 3. auto-polish-loop: 自动循环磨光

**用途**: 多轮循环（审查 → 修复），直到无 P0/P1 或达到最大轮数

**命令**:
```bash
python super_review_agent.py auto-polish-loop \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --skill-name doc-fixer-claude \
  --max-rounds 5 \
  --output tmp/polished.md \
  --verbose
```

**输出**:
- `tmp/polished_rounds/` 目录:
  - `round_0_original.md` - 原始文档
  - `round_1_review.md` - 第1轮审查报告
  - `round_1_fixed.md` - 第1轮修复结果
  - `round_2_review.md` - 第2轮审查报告
  - `round_2_fixed.md` - 第2轮修复结果
  - ...
  - `final_review.md` - 最终审查报告（如达到最大轮数）
- `tmp/polished.md` - 最终文档

**日志示例**:
```
======================================================================
[Round 1/5]
======================================================================
[Round 1/Step 1] 正在调用 Codex 审查...
  中间文件: tmp/polished_rounds/round_1_review.md
  统计: P0 缺陷 3个, P1 缺陷 5个
[Round 1/Step 2] 正在调用 Claude 修复...
  中间文件: tmp/polished_rounds/round_1_fixed.md

======================================================================
[Round 2/5]
======================================================================
[Round 2/Step 1] 正在调用 Codex 审查...
  中间文件: tmp/polished_rounds/round_2_review.md
  统计: P0 缺陷 0个, P1 缺陷 1个
[Round 2] 🎉 已无 P0/P1 缺陷，磨光完成！
✓ 最终文档已保存至: tmp/polished.md
  总轮数: 2/5 轮
```

**适用场景**:
- 文档质量问题较多
- 需要达到"无 P0/P1"的严格标准
- 自动化文档精修流程

---

### 4. quick-check: 快速检测

**用途**: 只检测是否存在 P0/P1，不生成完整报告

**命令**:
```bash
python super_review_agent.py quick-check \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --verbose
```

**返回码**:
- `0` - 无 P0/P1 缺陷
- `1` - 有 P0/P1 缺陷或错误

**输出**:
```
[INFO] 统计: P0 缺陷 0个, P1 缺陷 0个
[INFO] ✓ 文档质量良好，无 P0/P1 缺陷
```

**适用场景**:
- CI/CD 管道中的快速检查
- Git pre-commit hook
- 定期健康检查

---

## 🛠️ 完整参数说明

### 通用参数

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--doc` | 待审查文档的路径 | ✅ | - |
| `--codex-prompt` | Codex 审查 prompt 文件路径 | ✅ | - |
| `--codex-cmd` | Codex 命令（如果不在 PATH 中） | ❌ | `codex` |
| `--timeout` | 命令超时时间（秒） | ❌ | `600` (10分钟) |
| `--verbose` | 启用详细日志 | ❌ | `False` |

### fix-once / auto-polish-loop 额外参数

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--claude-cmd` | Claude 命令（如果不在 PATH 中） | ❌ | `claude` |
| `--skill-name` | Claude Skill 名称 | ✅ | - |
| `--output` | 修复后文档输出路径 | ✅ | - |

### auto-polish-loop 额外参数

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--max-rounds` | 最大循环轮数 | ❌ | `3` |

---

## 🐛 常见问题排查

### 1. `Codex 命令未找到`

**问题**:
```
[ERROR] Codex 命令未找到: codex
[ERROR] 请确保 Codex CLI 已安装并在 PATH 中
```

**解决方案**:

**方案 A**: 将 Codex 添加到 PATH
```bash
# Windows: 编辑系统环境变量
# 添加: C:\Users\<你的用户名>\AppData\Roaming\npm

# macOS/Linux: 编辑 ~/.bashrc 或 ~/.zshrc
export PATH="$PATH:$HOME/.npm-global/bin"
```

**方案 B**: 使用完整路径
```bash
python super_review_agent.py review-only \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" \
  --output tmp/review.md
```

---

### 2. `无法解析审查报告中的 P0/P1 数量`

**问题**:
```
[WARNING] ⚠️  所有解析方法都未能提取 P0/P1 数量
[WARNING] 可能原因：审查报告格式不符合预期，或报告内容为空
```

**原因**:
Codex 返回的审查报告格式不符合预期（7 种解析方法都无法匹配）

**解决方案**:
1. 手动检查审查报告内容
2. 调整 `reviewer_prompt.txt`，明确要求格式：
   ```
   ## 摘要
   - P0 缺陷: X个
   - P1 缺陷: Y个
   ```

---

### 3. `Claude 返回了空文档`

**问题**:
```
[ERROR] [Round 1] ✗ Claude 返回了空文档，修复失败
[ERROR]   建议检查审查报告格式或 Claude Skill 配置
```

**原因**:
Claude 未能正确解析审查报告或执行修复

**解决方案**:
1. 检查审查报告格式是否清晰
2. 检查 `--skill-name` 是否正确
3. 尝试使用 `fix-once` 模式手动验证

---

### 4. Windows 环境下 Claude CLI 需要 git-bash

**问题**:
```
[ERROR] Claude Code on Windows requires git-bash (https://git-scm.com/downloads/win)
[ERROR] If installed but not in PATH, set environment variable pointing to your bash.exe
```

**原因**:
Claude CLI 在 Windows 上依赖 git-bash 环境

**解决方案**:

**方案 A**: 设置环境变量（推荐 - 永久生效）
```bash
# 设置系统环境变量
# 1. 打开"系统属性" → "环境变量"
# 2. 添加用户变量或系统变量：
#    变量名: CLAUDE_CODE_GIT_BASH_PATH
#    变量值: D:\Program Files\Git\usr\bin\bash.exe
# 3. 重新打开命令行窗口
```

**方案 B**: 临时设置环境变量（单次会话）
```bash
# 在运行脚本前设置环境变量
set CLAUDE_CODE_GIT_BASH_PATH=D:\Program Files\Git\usr\bin\bash.exe

# 然后运行脚本
python super_review_agent.py fix-once \
  --doc docs/API.md \
  --codex-prompt prompts/reviewer.txt \
  --skill-name doc-fixer-claude \
  --output tmp/fixed.md
```

**方案 C**: 使用 cmd /c 包装（推荐用于自动化脚本）
```bash
cmd /c "set CLAUDE_CODE_GIT_BASH_PATH=D:\Program Files\Git\usr\bin\bash.exe && python super_review_agent.py fix-once --doc docs/API.md --codex-prompt prompts/reviewer.txt --skill-name doc-fixer-claude --output tmp/fixed.md"
```

**查找 bash.exe 位置**:
```bash
where bash.exe
# 典型输出:
# D:\Program Files\Git\usr\bin\bash.exe
# C:\Program Files\Git\bin\bash.exe
```

---

### 5. Windows UTF-8 编码问题

**问题**:
```
UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f680'
```

**解决方案**:
已在 v2.0 中修复！`setup_logging()` 会自动设置 UTF-8 编码。

如果仍有问题，请确保使用 Python 3.8+ 并更新到最新版本。

---

## 📦 项目实战示例

### 示例 1: AI 广告代投系统 - DDD 架构文档审查

**场景**: 审查 `DDD_API_ARCHITECTURE_polished.md` 文档

**步骤 1**: 创建审查 prompt
```bash
cat > test_super_review/reviewer_prompt.txt << 'EOF'
请审查以下文档，检查是否存在以下问题：

## P0 缺陷（阻塞性问题）
- 与 SoT 文档冲突的定义（如状态机、数据字段、API 路径）
- 重复定义已在 SoT 中定义的内容
- 缺少关键章节或信息不完整

## P1 缺陷（重要问题）
- 示例代码与文档说明不一致
- 缺少必要的引用声明或版本信息
- 架构图或流程图缺失或不清晰

请按以下格式输出审查报告：

---
# 文档审查报告

## 摘要
- P0 缺陷: X个
- P1 缺陷: Y个

## P0 缺陷列表
（如有）

## P1 缺陷列表
（如有）

## 建议
（如有）
---
EOF
```

**步骤 2**: 运行自动磨光模式
```bash
python super_review_agent.py auto-polish-loop \
  --doc docs/3.dev-guides/DDD_API_ARCHITECTURE_polished.md \
  --codex-prompt test_super_review/reviewer_prompt.txt \
  --skill-name doc-fixer-claude \
  --max-rounds 3 \
  --output test_super_review/DDD_ARCH_final.md \
  --verbose
```

**步骤 3**: 查看结果
```bash
# 查看最终文档
cat test_super_review/DDD_ARCH_final.md

# 查看所有轮次
ls test_super_review/DDD_ARCH_final_rounds/
```

---

## 🎯 最佳实践

### 1. 审查 Prompt 编写建议

**✅ 好的 Prompt**:
```
请审查文档，检查以下问题：

## P0 缺陷（阻塞性）
1. 与 STATE_MACHINE.md v2.6 冲突的状态定义
2. 重复定义已在 DATA_SCHEMA.md v5.2 中定义的表结构
3. 缺少 SoT 引用声明

## P1 缺陷（重要）
1. 示例代码与说明不一致
2. 缺少必要的架构图

输出格式：
---
## 摘要
- P0 缺陷: X个
- P1 缺陷: Y个
---
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
| 小型 (< 500 行) | 300s (5分钟) | Codex/Claude 快速响应 |
| 中型 (500-2000 行) | 600s (10分钟) | 默认值 |
| 大型 (> 2000 行) | 1200s (20分钟) | 大文档处理时间更长 |

---

## 🔧 高级用法

### 1. 集成到 CI/CD 管道

**GitHub Actions 示例**:
```yaml
name: Doc Quality Check

on: [pull_request]

jobs:
  doc-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install Codex CLI
        run: npm install -g codex-cli

      - name: Run Quick Check
        run: |
          python super_review_agent.py quick-check \
            --doc docs/API.md \
            --codex-prompt .github/reviewer_prompt.txt

      - name: Fail if defects found
        if: failure()
        run: echo "❌ P0/P1 缺陷检测失败，请修复后重新提交"
```

### 2. Git Pre-commit Hook

**`.git/hooks/pre-commit`**:
```bash
#!/bin/bash

# 检查所有变更的 .md 文档
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.md$'); do
    echo "检查文档: $file"
    python super_review_agent.py quick-check \
        --doc "$file" \
        --codex-prompt .github/reviewer_prompt.txt

    if [ $? -ne 0 ]; then
        echo "❌ 文档 $file 存在 P0/P1 缺陷，请修复后再提交"
        exit 1
    fi
done

echo "✓ 所有文档通过质量检查"
```

---

## 📊 性能指标

**基于 AI 广告代投系统测试数据** (文档: DDD_API_ARCHITECTURE_polished.md, 40KB):

| 模式 | 平均耗时 | 资源占用 | 成功率 |
|------|---------|---------|--------|
| quick-check | 30-60s | 低 | 95% |
| review-only | 45-90s | 中 | 90% |
| fix-once | 90-180s | 中 | 85% |
| auto-polish-loop (3轮) | 5-10分钟 | 高 | 80% |

---

## 📚 相关资源

- **Codex CLI 文档**: https://github.com/codex-cli/codex
- **Claude CLI 文档**: https://docs.anthropic.com/claude/cli
- **项目 SoT 文档**: `docs/2.sot/`
- **测试报告**: `test_super_review/TEST_REPORT.md`

---

**最后更新**: 2025-11-24 | **版本**: v2.0 (稳健性增强版)
