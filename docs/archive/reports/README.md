# Reports Archive

> **归档日期**: 2025-12-18
> **归档原因**: 清理项目根目录，集中管理历史报告

---

## 目录结构

```
reports/
├── bug-fixes/          # Bug 修复报告
│   ├── BUG_FIX_REPORT_FINAL.md    # 最终版本 ★
│   ├── BUG_FIX_REPORT_v2.1.md
│   └── BUG_FIX_REPORT_v2.2.md
├── test-reports/       # 测试报告
│   ├── TEST_REPORT_v2.3_FINAL.md  # 最终版本 ★
│   ├── TEST_REPORT_v2.1.md
│   ├── QA_TEST_EXECUTION_REPORT.md
│   ├── REGRESSION_REPORT_2025-12-02.md
│   ├── PROJECTS_TEST_RESULTS_SUMMARY.md
│   └── RECONCILIATION_TEST_FIX_SUMMARY.md
├── agent-reports/      # Agent 相关报告
│   ├── SUPER_REVIEW_AGENT_FINAL_SUMMARY.md
│   └── SUPER_REVIEW_AGENT_USAGE.md
└── progress-reports/   # 开发进度报告
    └── DEVELOPMENT_PROGRESS_REPORT.md
```

---

## 归档策略

### 保留最新版本
- `*_FINAL.md` 或最高版本号的文件为当前有效版本
- 旧版本保留供历史追溯

### 访问方式
- 仅供历史查询，不应作为当前开发依据
- 新报告应放在 `docs/8.testing/` 或项目 CI/CD 产物中

### 清理周期
- 每季度审查一次
- 超过 6 个月的旧版本可考虑删除

---

**归档执行**: Claude Code
**文档结构问题修复**: P0.4
