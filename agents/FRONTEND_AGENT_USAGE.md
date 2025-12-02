# 前端子代理（FEAgent）使用指南

本文档说明如何利用 FEAgent 或编排器（OrchestratorAgent）批量生成前端代码，适用于已经完成设计/后端接口的 8 个模块场景。

## 前置条件
- 已配置 LLM 后端（Anthropic API 或 Claude Code CLI），可用性可通过 `python -m agents.cli status` 检查。
- 前端模块的需求/设计描述已确定，并且目标文件路径清晰（相对 `frontend/` 目录）。
- 默认行为为 **dry-run**：FEAgent 和前端编排流都会先返回变更 JSON，不直接写盘，便于审核。

## 核心命令速查
1. 查看后端状态与可用 Agent：
   ```bash
   python -m agents.cli status
   ```
2. 调用 FEAgent 生成单个模块：
   ```bash
   python -m agents.cli run fe \
     --action "实现 <模块名> 前端" \
     --files "app/<module>/page.tsx,app/<module>/components/<Widget>.tsx"
   ```
   - `--action` 用于描述模块需求，内部会作为 `task` 传递给 FEAgent。
   - `--files` 列出需要生成/重构的 TSX/TS 文件（相对 `frontend/` 路径，逗号分隔）。
   - 结果中的 `changes` 字段给出完整文件内容，可在确认后写回。
3. 使用编排器跑前端重构流水线（含 SoT 审核，可选写盘）：
   ```bash
   # 仅预览（默认）
   python -m agents.cli run orch --action frontend_restructure --task "重构前端结构"

   # 自动写入生成的文件
   python -m agents.cli run orch --action frontend_restructure --task "重构前端结构" --auto-write
   ```
   - 流水线会生成结构规格文档、调用 FEAgent 产出代码、再经过 SoT Guard 审核。
   - `--auto-write` 为真时，审核通过的文件会落盘到 `frontend/`。

## 8 个模块的推荐批量流程
> 适用于“8 个模块均已完成设计/后端联调”的场景。

1. **准备模块列表**：将 8 个模块命名为 `module1`~`module8`，并整理各自的目标文件清单，例如：
   - `app/module1/page.tsx`
   - `app/module1/components/Table.tsx`
   - `app/module2/page.tsx`
   - …
2. **依次调用 FEAgent（推荐脚本循环）**：
   ```bash
   modules=(module1 module2 module3 module4 module5 module6 module7 module8)
   for m in "${modules[@]}"; do
     python -m agents.cli run fe \
       --action "实现 ${m} 前端" \
       --files "app/${m}/page.tsx,app/${m}/components/${m^}Widget.tsx"
   done
   ```
   - 将 `--files` 替换为实际文件列表，必要时追加更多逗号分隔路径。
   - 输出的 `changes` 可保存到临时目录或直接写回对应文件。
3. **集中写盘（可选）**：如果希望一次性落盘且经过审核，可在确认 FEAgent 输出后，使用编排器 dry-run 生成变更，再加 `--auto-write` 写入：
   ```bash
   python -m agents.cli run orch --action frontend_restructure --task "合并 8 个模块的前端代码" --auto-write
   ```
4. **人工检查与提交**：核对生成的 TSX/TS 内容、运行前端 lint/test，确认后再提交到版本库。

## 常见提示
- FEAgent 默认不会写文件；需要自动写盘时请使用编排器并开启 `--auto-write`。
- 如果模型返回 JSON 解析错误，可查看输出中的 `raw` 片段定位问题再重试。
- 尽量在 `--action` 中描述清楚交互、状态和依赖的 API，能显著提升生成质量。

## 如何将 FEAgent 输出写入文件（手动模式）
当未使用 `--auto-write` 时，可根据 `changes` 数组手动保存文件：

1. FEAgent 会返回形如 `{"path": "app/module1/page.tsx", "content": "..."}` 的对象列表，路径相对 `frontend/`。
2. 推荐在 `frontend/` 下执行以下脚本，将内容写盘（假设已将响应保存到 `result.json`）：
   ```bash
   cd frontend
   jq -r '.changes[] | "echo \(.content | @sh) > \(.path)"' ../result.json | bash
   ```
   - 如果 `jq` 不可用，可逐条复制 `content` 覆盖到对应文件。
3. 写盘后运行 `pnpm lint`/`pnpm test` 或 `npm run lint`/`npm test` 验证生成代码。
