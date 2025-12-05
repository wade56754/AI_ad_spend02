---
name: agent-platform-orchestrator
description: >
  当需要对 AI_ad_spend02 项目进行后端生成、前端生成、测试修复、文档对齐等自动化操作时，
  使用本 Skill 规划并生成标准化的 agent_platform 调用方案和 CLI 命令，
  始终通过 orchestrator 执行，而不是在对话中直接随意改代码。
---

# Agent Platform Orchestrator Skill

## 1. Skill 概要

本 Skill 的唯一职责：

> 帮用户把自然语言需求转换成 **规范、可执行、可复盘的 agent_platform 调用计划**，  
> 包含：flow / mode / 目标文件 / CLI 命令 / 执行顺序 / 结果解读策略。

**本 Skill 不直接生成或修改项目代码文件**，所有实际变更应通过 `agent_platform` 的 orchestrator 完成。

---

## 2. 适用场景（何时使用本 Skill）

当满足以下任一条件时，应优先考虑使用本 Skill：

- 用户显式提到：
  - "用 agent_platform…"
  - "orch flow / orchestrator / be_then_test / gen_backend"
  - "自动修复测试 / 自动生成后端 / 自动生成前端"
- 用户目标是基于 **AI_ad_spend02** 项目现有 Agent/Flow：
  - 生成 / 更新后端模块代码
  - 生成 / 重构前端模块代码
  - 运行并修复相关测试
  - 对齐代码与 SoT 文档（STATE_MACHINE / BUSINESS_RULES / API_SOT 等）
- 用户希望使用 CLI 执行自动化任务，而不是让 Claude 直接编写大量代码。

---

## 3. 禁用场景（不要使用本 Skill）

出现以下情况时，不要使用本 Skill，应明确对用户说明：

- 当前上下文与 **AI_ad_spend02** 无关，或项目路径不明确。
- 用户在一个完全不同的代码库中工作，且未提到 agent_platform。
- 用户要求直接在生产环境 / 生产服务器上执行命令。
- 用户仅希望：
  - 头脑风暴架构方案
  - 纯文档撰写
  - 与 agent_platform 无关的临时小脚本。

在这些场景中，应回退为普通对话 / 其他 Skill，而不是调用本 Skill。

---

## 4. 前置假设

本 Skill 假定以下条件：

- 用户在本机已有可用的 `agent_platform` 环境：
  - 已克隆 `AI_ad_spend02` 仓库；
  - 已创建并配置虚拟环境（如 `.venv`）；
  - `agent_platform.cli` 可被 `python -m agent_platform.cli` 正常调用。
- 项目根路径可以由用户确认，例如：
  - `D:\git\1108\AI_ad_spend02`。
- 用户可以在终端（PowerShell / Bash 等）执行命令，并能复制执行输出回到对话中。

如上述假设不成立，应先引导用户完成环境配置，而不是直接给出 orch 命令。

---

## 5. 输入字段定义

在生成任何命令前，必须先从用户需求中推导出以下 4 个字段：

### 5.1 target_module（目标模块）

- 示例：`ledger`, `topup`, `reconciliation`, `finance_profit`, `ad_spend`, `frontend_dashboard` 等。
- 用途：
  - 用于在 `--task` 中文本描述中说明这次操作的作用域；
  - 可用于推导默认的 `--target-files`（例如 ledger 对应 `backend/services/ledger_service.py`）。

### 5.2 flow（执行流类型）

必须与 `agent_platform` 实际支持的 flow 名称保持一致（以真实代码为准）。示例：

| flow           | 说明                                       |
|----------------|--------------------------------------------|
| `gen_backend`  | 批量/单模块生成或更新后端代码，不自动跑测试 |
| `be_then_test` | 先生成/更新后端代码，再运行对应测试         |

当不确定时：

- 用户需要"生成 / 修改代码 + 立刻跑测试" → 优先推荐 `be_then_test`；
- 用户只想先生成代码，测试稍后再手动跑 → 推荐 `gen_backend`。

### 5.3 mode（执行模式）

用于区分"计划 / 实际写入"等模式，至少支持：

- `plan`：规划模式（dry-run），只生成计划/补丁/修改说明，不真正写入代码文件；
- `apply`：执行模式，允许 orchestrator 真正写入文件并修改代码。

若用户未明确说明，应默认选择 **`mode=plan`**。

### 5.4 scope / target-files（影响范围）

- `scope`：用户用自然语言描述的影响范围，例如：
  - "ledger 状态机相关服务和测试"；
  - "对账批次 API & 对应测试"。
- `target-files`：映射为 CLI 参数 `--target-files` 的值：
  - 多个文件 / 目录用逗号分隔；
  - 示例：`backend/services/ledger_service.py,backend/tests`。

**约束：**

- 不要随意扩大战争范围，只列出与当前任务高度相关的文件/目录；
- 若不确定具体文件路径，应向用户确认，而不是凭空猜测。

---

## 6. 标准使用流程（SOP）

### Step 1：复述并澄清任务目标

1. 用 1～2 句话，用中文复述用户想要达成的结果，并指出模块/范围，例如：

   > "目标：修复 AI_ad_spend02 中与对账批次状态机相关的 ledger 测试失败问题，使相关 pytest 用例全部通过。"

2. 如果以下信息缺失，应向用户补问：
   - 操作模块（target_module）；
   - 大致影响范围（scope）；
   - 是否允许这次操作真正写入文件（auto-write 策略）。

### Step 2：推导 flow / mode / target-files

遵循以下规则：

1. 根据用户目标选择 `flow`：
   - "生成 / 更新后端 + 立刻跑测试" → `be_then_test`；
   - "只生成/更新后端，不跑测试" → `gen_backend`。
2. 默认选择 `mode=plan`，除非用户明确接受实际写入。
3. 根据目标模块和影响范围推导 `target-files`，例如：
   - ledger 相关逻辑：
     - `backend/services/ledger_service.py`；
     - `backend/tests`。
   - finance_profit：
     - `backend/schemas/profit.py`；
     - `backend/routers/finance_profit.py`；
     - `backend/tests/api/test_finance_profit_flow_generated.py`。

### Step 3：生成 CLI 命令模板

#### 3.1 PowerShell（推荐用于 Windows）

**永远不要在示例中硬编码用户机器路径**，应使用占位符：

```powershell
cd {{PROJECT_ROOT}}    # 例如 D:\git\1108\AI_ad_spend02
{{VENV_ACTIVATE}}      # 例如 .\.venv\Scripts\Activate.ps1

python -m agent_platform.cli orch `
  --flow {{FLOW_NAME}} `
  --mode {{MODE}} `
  --task "{{用中文精确描述这次任务}}" `
  --target-files "{{逗号分隔的文件或目录}}" `
  --auto-write {{True/False}}
```

生成命令时必须：

- 将 `{{FLOW_NAME}}`、`{{MODE}}`、`target-files` 替换为前面推导出的值；
- `--task` 内容使用简洁但明确的中文，描述：
  - 本次操作意图；
  - 涉及模块；
  - 是否只规划不执行（例如强调"只给出修改计划，不真正生成代码"）。

#### 3.2 Bash（适用于 Linux / WSL，可选）

在用户明确表示使用 Bash/Linux 时，可以给出一份 Bash 版本：

```bash
cd {{PROJECT_ROOT}}    # 例如 /home/user/AI_ad_spend02
source {{VENV_ACTIVATE}}  # 例如 .venv/bin/activate

python -m agent_platform.cli orch \
  --flow {{FLOW_NAME}} \
  --mode {{MODE}} \
  --task "{{用中文精确描述这次任务}}" \
  --target-files "{{逗号分隔的文件或目录}}" \
  --auto-write {{True/False}}
```

---

## 7. auto-write 安全策略（必须遵守）

### 7.1 默认策略

- 首次建议时必须使用：`--auto-write False`；
- 即使用户没有明确提 dry-run，也不要主动设为 True。

### 7.2 允许 --auto-write True 的条件

只有同时满足以下条件，才可以建议 `--auto-write True`：

- 用户已经看过 `mode=plan` 的输出，并确认修改方向；
- 用户明确表示接受自动写文件，例如：
  - "可以让它自动写入代码，不用一条条手动改。"

每一次将 `auto-write` 设为 `True` 的建议，回答中都必须再次提醒风险：

> "注意：此命令会直接修改 {{target-files}} 中的文件，请确保已在正确分支/环境执行。"

---

## 8. 指导用户执行并回传结果

在给出命令后，应指导用户：

1. 在终端中执行上述命令；
2. 执行完毕后，至少复制以下部分输出回对话中：
   - Flow 名称与 Run ID；
   - 整体状态：SUCCESS / FAILED；
   - 生成 / 修改的文件列表；
   - 测试通过 / 失败 / 错误数量；
   - 关键错误堆栈或 Assertion 信息。

---

## 9. 解读结果并规划下一轮动作

拿到用户粘贴的输出后，应按以下策略处理：

### 若整体状态为 FAILED：

- 从日志中找出 3～5 条最重要的错误（按影响范围和阻塞程度排序）；
- 针对每个关键错误，生成更细粒度的下一轮 `--task` 文案建议；
- 可以建议用户再次以 `mode=plan` 运行新的任务。

### 若状态为 SUCCESS 但测试仍有失败：

- 列出失败测试的文件与用例名称；
- 针对每组失败测试生成具体的修复任务描述；
- 再次使用 `be_then_test` 或其他合适 flow 规划修复动作。

### 若状态为 SUCCESS 且关联测试全部通过：

- 生成简短的"模块修复完成"总结；
- 如有需要，建议用户：
  - 更新相关 SoT 文档（如有变更）；
  - 生成 Freeze 报告（可以交给其他文档类 Skill 处理）。

---

## 10. 输出格式要求（对 Claude 的硬约束）

当用户说"用 agent_platform 帮我 xxx"时，本 Skill 的输出必须包含以下四部分：

### 任务摘要

1 段话，重述用户目标 + 影响模块，例如：

> "目标：使用 agent_platform 在 AI_ad_spend02 中修复 ledger 对账批次相关测试，使对应 pytest 用例全部通过。"

### 参数建议

以清单形式列出：

- `target_module`: ...
- `flow`: ...
- `mode`: ...
- `target-files`: ...
- `auto-write`: False（首次必为 False）

### 完整 CLI 命令

- 至少给出一份 PowerShell 版本；
- 允许使用占位符 `{{PROJECT_ROOT}}` 和 `{{VENV_ACTIVATE}}`；
- 必须包含 `--flow` / `--mode` / `--task` / `--target-files` / `--auto-write`。

### 后续操作提醒

告知用户：

- 先在终端执行命令；
- 执行后将输出关键部分复制回来。
- 明确说明下一轮你能帮用户做什么（例如"解读日志并生成下一轮任务计划"）。

---

## 11. 示例：修复 ledger 对账测试（示范用法）

### 11.1 用户请求示例

> "用 agent_platform 帮我修复 ledger 模块中和对账批次状态机相关的测试失败问题，让这些测试全部通过。"

### 11.2 期望的参数推导结果

- `target_module`: ledger
- `flow`: be_then_test
- `mode`: plan
- `target-files`: backend/services/ledger_service.py,backend/tests
- `auto-write`: False

### 11.3 期望的命令示例（PowerShell）

```powershell
cd {{PROJECT_ROOT}}    # 例如 D:\git\1108\AI_ad_spend02
{{VENV_ACTIVATE}}      # 例如 .\.venv\Scripts\Activate.ps1

python -m agent_platform.cli orch `
  --flow be_then_test `
  --mode plan `
  --task "修复 ledger 模块中与对账批次状态机相关的测试失败问题，只给出修改计划和目标文件列表，不真正生成代码。" `
  --target-files "backend/services/ledger_service.py,backend/tests" `
  --auto-write False
```

随后，在用户贴回 orch 输出日志后，本 Skill 应按照第 9 节的规则解析结果，并给出下一步建议（例如：针对具体失败测试生成更细分的任务，再次规划 flow / mode / target-files）。

---

## 12. 安全与限制

本 Skill 不得：

- 擅自扩大 `target-files` 范围；
- 在用户未同意的情况下建议 `auto-write=True`；
- 在未通过 orchestrator 的前提下，直接生成大规模代码改动。

如遇到不确定的 flow / mode / 参数含义：

- 应显式提示"不确定该 flow 是否存在或适用"；
- 建议用户在本地查看 agent_platform 源码或相关文档，而不是编造参数。

通过以上约束，确保 agent_platform 始终作为唯一的自动化执行入口，而 Claude 主要负责"理解需求 → 规划调用 → 解读结果"，避免失控修改代码。
