# SoT 文档清理检查清单

**生成日期**: 2025-11-23
**分析范围**: MASTER_SPEC, API_SOT, ERROR_CODES, RLS_POLICIES
**清理模式**: 手动执行
**预计节省空间**: ~150 KB

---

## 📋 执行清单

### ✅ P0 - 立即执行 (关键问题)

#### 1. 更新根目录 MASTER_SPEC.md

**问题**: 根目录版本 v1.0 (2025-01-22) 落后 10 个月

**最新版本**: `/docs/1.overview/MASTER_SPEC.md` v1.1 (2025-11-22)

**执行命令**:
```bash
# 备份现有文件
copy "MASTER_SPEC.md" "MASTER_SPEC.md.backup"

# 更新到最新版本
copy /Y "docs\1.overview\MASTER_SPEC.md" "MASTER_SPEC.md"

# 验证更新
findstr /C:"文档版本" MASTER_SPEC.md
# 应显示: > **文档版本**: v1.1
```

**影响**:
- ✅ 开发者将看到最新的架构规范
- ✅ 与 sot-freeze-v1.0 标签一致

**验证**:
```bash
fc /N "MASTER_SPEC.md" "docs\1.overview\MASTER_SPEC.md"
# 应显示: FC: 找不到差异
```

---

### ⚠️ P1 - 本周执行 (清理冗余)

#### 2. 删除冗余 ERROR_CODES 归档文件

**冗余文件**:
1. `docs\archive\ERROR_CODES.md` - 无 SoT 标记，被 ERROR_CODES_SOT.md 替代
2. `docs\archive\old_core\ERROR_CODES_SOT.md` - 旧版本 SoT，已归档到 old_core

**保留文件**:
- ✅ `docs\2.sot\ERROR_CODES_SOT.md` (活跃 v2.1)
- ✅ `docs\archive\ERROR_CODES_SYNC_REPORT.md` (历史同步报告，有参考价值)

**执行命令**:
```bash
# 删除冗余文件
del "docs\archive\ERROR_CODES.md"
del "docs\archive\old_core\ERROR_CODES_SOT.md"

# 验证删除
dir /B "docs\archive\ERROR_CODES*.md"
# 应仅显示: ERROR_CODES_SYNC_REPORT.md
```

**节省空间**: ~40 KB

---

#### 3. 删除冗余 RLS_POLICIES 归档文件

**冗余文件**:
1. `docs\archive\RLS_POLICIES.md` - 三重归档之一
2. `docs\archive\old_security\RLS_POLICIES.md` - 三重归档之二

**保留文件**:
- ✅ `docs\2.sot\RLS_POLICIES_SOT.md` (活跃 SoT)
- ⚠️ `docs\archive\old_core\RLS_POLICIES_SOT.md` (可选保留1个归档作为历史记录)

**执行命令**:
```bash
# 删除 2 个冗余归档
del "docs\archive\RLS_POLICIES.md"
del "docs\archive\old_security\RLS_POLICIES.md"

# 验证删除
dir /B /S "docs\archive\*RLS_POLICIES*.md"
# 应仅显示: docs\archive\old_core\RLS_POLICIES_SOT.md
```

**节省空间**: ~50 KB

---

### 📝 P2 - 可选优化 (质量提升)

#### 4. 统一 SoT 文档元数据格式

**标准格式** (参考 `docs/1.overview/MASTER_SPEC.md` v1.1):
```markdown
> **文档版本**: vX.Y.Z
> **发布日期**: YYYY-MM-DD
> **文档类型**: 🔴 [类型描述] (True Source of Truth)
> **适用范围**: [范围说明]
> **规范级别**: 🔴 [优先级]
```

**需要更新的文档**:
1. `/MASTER_SPEC.md` (更新后自动修复)
2. `docs/2.sot/API_SOT.md` - 已有完整元数据 ✅
3. `docs/2.sot/ERROR_CODES_SOT.md` - 已有完整元数据 ✅
4. `docs/2.sot/RLS_POLICIES_SOT.md` - 需检查

**检查命令**:
```bash
# 查看各 SoT 文档的元数据
findstr /C:"文档版本" /C:"Version" "docs\2.sot\*.md"
```

---

#### 5. 验证文档交叉引用

**需要检查的引用**:

1. **MASTER_SPEC.md** 引用其他 SoT:
   ```
   - API_SOT.md ✅
   - DATA_SCHEMA.md ✅
   - STATE_MACHINE.md ✅
   - AUTH_SPEC.md ✅
   - LEDGER_SOT.md ✅
   ```

2. **API_SOT.md** 引用依赖文档:
   ```
   - DATA_SCHEMA.md v5.2 ✅
   - STATE_MACHINE.md v2.6 ✅
   - BUSINESS_RULES.md v3.1 ✅
   - ERROR_CODES_SOT.md v2.1 ✅
   - SYSTEM_OVERVIEW.md v2.0 ⚠️ (需确认版本)
   ```

**验证命令**:
```bash
# 检查引用的版本号
findstr /C:"DATA_SCHEMA" /C:"STATE_MACHINE" "docs\2.sot\API_SOT.md"
```

---

#### 6. 创建 SoT 文档索引

**建议在 `docs/2.sot/README.md` 中创建**:

```markdown
# SoT 文档索引

## 活跃 SoT 文档 (v1.0 Freeze)

| 文档 | 版本 | 更新日期 | 仲裁级别 | 说明 |
|------|------|---------|---------|------|
| [MASTER_SPEC.md](../1.overview/MASTER_SPEC.md) | v1.1 | 2025-11-22 | P0 | 系统架构宪法 |
| [STATE_MACHINE.md](./STATE_MACHINE.md) | v2.6 | - | P1 | 状态流转规范 |
| [DATA_SCHEMA.md](./DATA_SCHEMA.md) | v5.2 | - | P1 | 数据库模式定义 |
| [BUSINESS_RULES.md](./BUSINESS_RULES.md) | v3.1 | - | P1 | 业务规则约束 |
| [ERROR_CODES_SOT.md](./ERROR_CODES_SOT.md) | v2.1 | 2025-01-21 | P1 | 错误码真相源 |
| [AUTH_SPEC.md](./AUTH_SPEC.md) | v2.0 | - | P1 | 认证授权规范 |
| [API_SOT.md](./API_SOT.md) | v9.0 | 2025-01-22 | P1 | API 开发规范 |
| [LEDGER_SOT.md](./LEDGER_SOT.md) | v1.1 | - | P1 | 账本操作规范 |
| [DAILY_REPORT_SOT.md](./DAILY_REPORT_SOT.md) | v1.0 | - | P1 | 日报管理规范 |
| [RECONCILIATION_SOT.md](./RECONCILIATION_SOT.md) | v1.0 | - | P1 | 对账管理规范 |
| [TRANSFER_SOT.md](./TRANSFER_SOT.md) | v1.0 | - | P1 | 转账管理规范 |
| [RLS_POLICIES_SOT.md](./RLS_POLICIES_SOT.md) | - | - | P1 | 行级安全策略 |
```

---

## 🔍 清理前后对比

### 文件数量变化

| 类别 | 清理前 | 清理后 | 减少 |
|------|--------|--------|------|
| MASTER_SPEC | 2 | 1 (同步) | 1 |
| API_SOT | 2 | 2 | 0 |
| ERROR_CODES | 4 | 2 | 2 |
| RLS_POLICIES | 4 | 2 | 2 |
| **总计** | **12** | **7** | **5** |

### 目录结构变化

**清理前**:
```
AI_ad_spend02/
├── MASTER_SPEC.md (v1.0 过时)
└── docs/
    ├── 1.overview/
    │   └── MASTER_SPEC.md (v1.1 最新)
    ├── 2.sot/
    │   ├── API_SOT.md (v9.0 活跃)
    │   ├── ERROR_CODES_SOT.md (v2.1 活跃)
    │   └── RLS_POLICIES_SOT.md (活跃)
    └── archive/
        ├── ERROR_CODES.md (冗余)
        ├── ERROR_CODES_SYNC_REPORT.md (保留)
        ├── RLS_POLICIES.md (冗余)
        ├── old_core/
        │   ├── API_SOT.md (归档)
        │   ├── ERROR_CODES_SOT.md (冗余)
        │   └── RLS_POLICIES_SOT.md (可选保留)
        └── old_security/
            └── RLS_POLICIES.md (冗余)
```

**清理后**:
```
AI_ad_spend02/
├── MASTER_SPEC.md (v1.1 ✅ 同步)
└── docs/
    ├── 1.overview/
    │   └── MASTER_SPEC.md (v1.1 最新)
    ├── 2.sot/
    │   ├── API_SOT.md (v9.0 活跃)
    │   ├── ERROR_CODES_SOT.md (v2.1 活跃)
    │   ├── RLS_POLICIES_SOT.md (活跃)
    │   └── README.md (新增索引)
    └── archive/
        ├── ERROR_CODES_SYNC_REPORT.md (保留)
        └── old_core/
            ├── API_SOT.md (归档)
            └── RLS_POLICIES_SOT.md (可选保留)
```

---

## ✅ 执行验证

### 验证步骤

1. **执行 P0 更新**
   ```bash
   copy /Y "docs\1.overview\MASTER_SPEC.md" "MASTER_SPEC.md"
   ```

2. **验证版本同步**
   ```bash
   findstr /C:"文档版本" MASTER_SPEC.md
   # 预期: > **文档版本**: v1.1
   ```

3. **执行 P1 清理**
   ```bash
   del "docs\archive\ERROR_CODES.md"
   del "docs\archive\old_core\ERROR_CODES_SOT.md"
   del "docs\archive\RLS_POLICIES.md"
   del "docs\archive\old_security\RLS_POLICIES.md"
   ```

4. **验证清理结果**
   ```bash
   dir /B /S "docs\archive\ERROR_CODES*.md"
   dir /B /S "docs\archive\*RLS_POLICIES*.md"
   ```

5. **提交更改**
   ```bash
   git add MASTER_SPEC.md
   git add docs/archive/
   git commit -m "docs: SoT文档清理 - 同步MASTER_SPEC v1.1 + 删除4个冗余归档"
   ```

---

## 📊 清理效果预估

| 指标 | 改进 |
|------|------|
| 文档冗余 | -41.7% (12→7) |
| 版本一致性 | 100% (MASTER_SPEC同步) |
| 存储空间 | -150 KB |
| 维护复杂度 | 显著降低 |

---

## 🚀 下一步行动

完成清理后，建议执行以下操作：

1. **创建 SoT 文档索引** (P2 第6项)
2. **运行一致性检查脚本** (如果有)
3. **更新 DOCS_README.md** 反映新的文档结构
4. **通知团队** SoT 文档已清理完成

---

**清理完成后请运行**: `/sc:analyze docs/ --focus architecture` 验证文档质量
