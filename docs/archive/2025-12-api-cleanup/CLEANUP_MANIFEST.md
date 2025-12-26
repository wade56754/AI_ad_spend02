# API 文档清理清单

> **清理日期**: 2025-12-23
> **清理原因**: 合并冗余文档，统一到 API_SOT.md v9.3

---

## 归档文件

| 原路径 | 行数 | 归档原因 |
|--------|------|----------|
| `docs/API/API_SPEC_GUIDE_v2.0_CORE.md` | 485 | 与 API_SOT.md 功能重叠 |
| `docs/API/API_SPEC_DETAILED.md` | 492 | 与 API_SOT.md 功能重叠 |
| `docs/API/API_SPEC_EXAMPLES.md` | 827 | 与 API_SOT.md 功能重叠 |
| `docs/API/API_SPEC_SCHEMAS.md` | 639 | 与 API_SOT.md 功能重叠 |
| `docs/7.appendix/API_TEST_CASES.md` | 52 | 空壳文档，全是 TODO |

**总计**: 5 个文件, 2495 行

---

## 保留文件

| 路径 | 行数 | 用途 |
|------|------|------|
| `docs/2.sot/API_SOT.md` | 2497 | **主 SoT** - 端点级 API 规范 |
| `docs/3.dev-guides/API_DEVELOPMENT_FLOW.md` | 562 | 开发流程指南 |
| `docs/3.dev-guides/DDD_API_ARCHITECTURE.md` | 1394 | DDD 架构设计参考 |
| `docs/integration/API_INTEGRATION_CHECKLIST.md` | 716 | 前端 API 对接清单 |

---

## 迁移说明

归档的 `docs/API/` 目录原本用于指导 AI 编写 API 规格书，现已被 API_SOT.md v9.3 完全覆盖：

- **标准字段名**: API_SOT.md §13.1
- **HTTP 方法/状态码**: API_SOT.md §2
- **请求/响应格式**: API_SOT.md §4
- **错误码**: API_SOT.md §13.2
- **完整示例**: API_SOT.md §5-12 (各模块端点)

如需参考旧文档，请查阅本目录下的归档文件。
