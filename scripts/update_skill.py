import re

path = r'D:\project\AI_ad_spend02\.claude\skills\ai-ad-code-factory\SKILL.md'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update version in frontmatter
content = content.replace('version: "3.3"', 'version: "3.4"')
content = content.replace('last_reviewed: 2025-12-22', 'last_reviewed: 2025-12-24')

# 2. Add code-blocks-registry.md to baseline
content = content.replace(
    '  - AI_CODE_FACTORY_REFACTOR_PROPOSAL.md v1.0',
    '  - AI_CODE_FACTORY_REFACTOR_PROPOSAL.md v1.0\n  - code-blocks-registry.md v1.0'
)

# 3. Add Code Blocks First section after anti_hallucination_principles
code_blocks_section = '''

  <!-- ======================================================
       2.2 代码块优先原则 (Code Blocks First) [v3.4 新增]
       来源: knowledge/code-blocks-registry.md v1.0
  ====================================================== -->
  <code_blocks_first>
    **核心原则**: 代码块优先，减少重复编写

    ### 强制规则 (BLOCKING)

    | 规则 | 描述 | 违反后果 |
    |------|------|---------|
    | CB-001 | 生成代码前，必须先查询代码块注册表 | BLOCKING |
    | CB-002 | 如果存在匹配的代码块，必须使用代码块，禁止重新编写 | BLOCKING |
    | CB-003 | 代码块只能扩展，不能修改核心逻辑 | WARNING |
    | CB-004 | 使用代码块时必须标注 `# CodeBlock: {block_id}` | WARNING |

    ### 代码块优先查询流程

    ```
    用户需求 --> 提取关键词 --> 查询代码块注册表 --> 匹配成功?
                                                    |
                                               是 --> 使用代码块
                                               否 --> 进入搜索流程
    ```

    ### 代码块注册表索引 (16 个代码块)

    **前端代码块 (8个)**:
    | ID | 名称 | 关键词 |
    |----|------|--------|
    | CB-FE-001 | DataTable | 表格, 列表, table, 分页, 排序 |
    | CB-FE-002 | StatusBadge | 状态, 徽章, badge, 标签 |
    | CB-FE-003 | DataState | 加载, loading, empty, skeleton |
    | CB-FE-004 | ActionButtons | 操作, 按钮, action, 确认 |
    | CB-FE-005 | GlobalFilters | 筛选, filter, 日期, select |
    | CB-FE-006 | PageHeader | 页面标题, header, 面包屑 |
    | CB-FE-007 | ApprovalTimeline | 时间线, timeline, 审批流程 |
    | CB-FE-008 | FormDialog | 表单, form, 弹窗, dialog |

    **后端代码块 (8个)**:
    | ID | 名称 | 关键词 |
    |----|------|--------|
    | CB-BE-001 | Pagination | 分页, pagination, list |
    | CB-BE-002 | ResponseEnvelope | 响应, response, 封装 |
    | CB-BE-003 | ErrorCodes | 错误, error, 异常 |
    | CB-BE-004 | PermissionFilter | 权限, permission, 过滤, role |
    | CB-BE-005 | StateMachine | 状态机, state, transition |
    | CB-BE-006 | AuditLog | 审计, audit, 日志, history |
    | CB-BE-007 | LedgerEntry | 账本, ledger, 余额, balance |
    | CB-BE-008 | KPICalculator | KPI, ROAS, CPL, CPA, 指标 |

    **详细代码模板**: knowledge/code-blocks-registry.md
  </code_blocks_first>

'''

# Insert after </anti_hallucination_principles>
content = content.replace(
    '  </anti_hallucination_principles>',
    '  </anti_hallucination_principles>' + code_blocks_section
)

# 4. Add version note
version_note = '''    ### v3.4 (2025-12-24) - 代码块优先版
    - 新增 `<code_blocks_first>` 章节
    - 新增 Phase 0: CODE BLOCKS CHECK (代码块检查)
    - 集成代码块注册表 (knowledge/code-blocks-registry.md)
    - 16 个代码块索引 (前端 8 个 + 后端 8 个)
    - 强制规则: CB-001 ~ CB-004
    - 核心原则: 代码块优先，减少重复编写

'''

content = content.replace(
    '    ### v3.3 (2025-12-24)',
    version_note + '    ### v3.3 (2025-12-24)'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated SKILL.md to v3.4 with Code Blocks First')
