# AI广告代投管理系统

## 定位
广告投放业务的"人、账户、项目、钱"管理系统，让账目清清楚楚、有据可查。

## 当前阶段
**Phase 1**：只提示、不阻断、不自动问责。老板是最终裁决人。

## 不变量（绝对不能违反）
1. **预收款≠收入**：履约完成前是负债
2. **平台消耗不含手续费**：广告费和手续费分开核算
3. **可用资金公式**：`opening_balance + Σtopup - Σad_spend`
4. **锁定后不可改**：只能红冲（ref_id + reason）
5. **数据域隔离**：投手只看自己账户，项目负责人只看自己项目

## 开发前必做
1. 查 `docs/sot/INDEX.md` 找到对应规格章节
2. 查 `docs/sot/MASTER.md` 确认规则
3. 检查状态机是否符合

## 常用命令
```bash
just dev              # 启动开发环境
just test             # 运行测试
just ci-check         # PR门禁
just release-check    # 上线门禁
```

## 关键文件
- **SoT**: `docs/sot/MASTER.md`（唯一真相源）
- **索引**: `docs/sot/INDEX.md`（模块→规格映射）
- **门禁**: `.ai-rules/quality-gates.md`
