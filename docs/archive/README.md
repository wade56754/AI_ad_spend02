# Documentation Archive

> **用途**: 归档历史文档、遗留版本和已完成的临时报告
> **管理策略**: 按日期或类别组织，保留历史追溯能力

---

## 目录结构

```
archive/
├── 2025-11-asdd-global-cleanup/   # ASDD 全局清理 (2025年11月)
├── 2025-11-dev-guides-legacy/     # Dev-Guides 遗留版本
├── 2025-11-overview-legacy/       # Overview 遗留版本
├── 2025-12-cleanup/               # 2025年12月清理
├── release/                       # 发布相关归档
└── reports/                       # 报告归档
    ├── bug-fixes/                 # Bug 修复报告
    ├── test-reports/              # 测试报告
    ├── agent-reports/             # Agent 相关报告
    └── progress-reports/          # 开发进度报告
```

---

## 归档类别

### 1. 日期归档 (YYYY-MM-*)
按时间组织的历史清理或迁移产物：
- `2025-11-asdd-global-cleanup/` - ASDD 框架建立时的全局清理
- `2025-11-dev-guides-legacy/` - Dev-Guides 层遗留文档
- `2025-11-overview-legacy/` - Overview 层遗留文档

### 2. 报告归档 (reports/)
从项目根目录移动的历史报告：
- 详见 [reports/README.md](./reports/README.md)

### 3. 发布归档 (release/)
版本发布相关的归档文档

---

## 归档策略

### 何时归档
| 情况 | 操作 |
|------|------|
| 文档被重写/替换 | 旧版本移入日期归档目录 |
| 临时报告完成使命 | 移入 `reports/` 对应子目录 |
| 版本发布 | 创建发布快照到 `release/` |
| 季度清理 | 整理过期文档到归档 |

### 保留期限
| 类型 | 保留期限 | 说明 |
|------|---------|------|
| SoT 遗留版本 | 永久 | 业务追溯需要 |
| 测试报告 | 1 年 | 质量追溯 |
| 进度报告 | 6 个月 | 项目管理参考 |
| 临时文档 | 3 个月 | 按需清理 |

### 命名规范
```
日期归档: YYYY-MM-{描述}
报告归档: 保持原文件名，按类型放入子目录
```

---

## 访问说明

### 查找历史版本
1. 确定文档所属层 (Overview/SoT/Dev-Guides/etc.)
2. 查找对应的日期归档目录
3. 按文件名或日期定位

### 恢复归档文档
1. 从归档目录复制到原位置
2. 更新版本号
3. 重新执行 ASDD 审计流程

---

## 相关文档

- 主文档索引: [../README.md](../README.md)
- 报告归档说明: [reports/README.md](./reports/README.md)
- ASDD 治理规范: [../1.overview/MASTER.md](../1.overview/MASTER.md)

---

**维护者**: Wade
**最后更新**: 2025-12-18
