# 代码验证报告

> 生成时间: 2025-12-18T08:28:55.103983

## 汇总

| 指标 | 数量 |
|------|------|
| 总文件数 | 7 |
| 通过 | 1 |
| 已修复 | 0 |
| 失败 | 6 |
| 跳过 | 0 |

## 错误

| 代码 | 文件:行 | 描述 |
|------|---------|------|
| `SOT-005` | `backend/services/daily_report_service.py:528` | 无效的错误码前缀: 'STATE' |
| `SOT-007` | `backend/services/daily_report_service.py:600` | 直接修改 balance 字段 |
| `SOT-001` | `backend/services/topup_service.py:95` | 无效的状态值: 'draft' |
| `SOT-001` | `backend/services/topup_service.py:110` | 无效的状态值: 'pending_review' |
| `SOT-001` | `backend/services/topup_service.py:210` | 无效的状态值: 'pending_review' |
| `SOT-001` | `backend/services/topup_service.py:218` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:254` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:263` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:316` | 无效的状态值: 'pending_review' |
| `SOT-001` | `backend/services/topup_service.py:316` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:377` | 无效的状态值: 'draft' |
| `SOT-001` | `backend/services/topup_service.py:377` | 无效的状态值: 'pending_review' |
| `SOT-001` | `backend/services/topup_service.py:438` | 无效的状态值: 'paid' |
| `SOT-001` | `backend/services/topup_service.py:515` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:527` | 无效的状态值: 'paid' |
| `SOT-001` | `backend/services/topup_service.py:536` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:537` | 无效的状态值: 'paid' |
| `SOT-001` | `backend/services/topup_service.py:564` | 无效的状态值: 'paid' |
| `SOT-001` | `backend/services/topup_service.py:587` | 无效的状态值: 'paid' |
| `SOT-001` | `backend/services/topup_service.py:643` | 无效的状态值: 'pending_review' |
| `SOT-001` | `backend/services/topup_service.py:644` | 无效的状态值: 'draft' |
| `SOT-001` | `backend/services/topup_service.py:645` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:646` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:647` | 无效的状态值: 'paid' |
| `SOT-001` | `backend/services/topup_service.py:657` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:657` | 无效的状态值: 'paid' |
| `SOT-001` | `backend/services/topup_service.py:663` | 无效的状态值: 'paid' |
| `SOT-001` | `backend/services/topup_service.py:680` | 无效的状态值: 'pending_review' |
| `SOT-001` | `backend/services/topup_service.py:680` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:724` | 无效的状态值: 'pending_review' |
| `SOT-001` | `backend/services/topup_service.py:725` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:726` | 无效的状态值: 'paid' |
| `SOT-001` | `backend/services/topup_service.py:731` | 无效的状态值: 'pending_review' |
| `SOT-001` | `backend/services/topup_service.py:731` | 无效的状态值: 'finance_approve' |
| `SOT-001` | `backend/services/topup_service.py:276` | 无效的状态值: 'finance_approved' |
| `SOT-005` | `backend/services/topup_service.py:320` | 无效的错误码前缀: 'STATE' |
| `SOT-005` | `backend/services/topup_service.py:381` | 无效的错误码前缀: 'STATE' |
| `SOT-005` | `backend/services/topup_service.py:441` | 无效的错误码前缀: 'STATE' |
| `SOT-007` | `backend/services/topup_service.py:485` | 直接修改 balance 字段 |
| `SOT-001` | `backend/services/transfer_service.py:45` | 无效的状态值: 'draft' |
| `SOT-001` | `backend/services/transfer_service.py:46` | 无效的状态值: 'pending_approval' |
| `SOT-001` | `backend/services/transfer_service.py:49` | 无效的状态值: 'pending_approval' |
| `SOT-001` | `backend/services/transfer_service.py:203` | 无效的状态值: 'draft' |
| `SOT-001` | `backend/services/transfer_service.py:283` | 无效的状态值: 'pending_approval' |
| `SOT-001` | `backend/services/transfer_service.py:291` | 无效的状态值: 'pending_approval' |
| `SOT-005` | `backend/services/transfer_service.py:287` | 无效的错误码前缀: 'STATE' |
| `SOT-005` | `backend/services/transfer_service.py:322` | 无效的错误码前缀: 'STATE' |
| `SOT-005` | `backend/services/transfer_service.py:360` | 无效的错误码前缀: 'STATE' |
| `SOT-005` | `backend/services/transfer_service.py:400` | 无效的错误码前缀: 'STATE' |
| `SOT-007` | `backend/services/transfer_service.py:458` | 直接修改 balance 字段 |
| `SOT-005` | `backend/routers/daily_reports.py:1286` | 无效的错误码前缀: 'STATE' |
| `SOT-005` | `backend/routers/daily_reports.py:1331` | 无效的错误码前缀: 'STATE' |
| `SOT-005` | `backend/routers/daily_reports.py:302` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:304` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:373` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:375` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:418` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:420` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:465` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:467` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:505` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:507` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:551` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:553` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:594` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:596` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:637` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:639` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:680` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:682` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:723` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:725` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:805` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:807` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:877` | 无效的错误码前缀: 'EMPTY' |
| `SOT-005` | `backend/routers/daily_reports.py:879` | 无效的错误码前缀: 'EMPTY' |
| `SOT-005` | `backend/routers/daily_reports.py:889` | 无效的错误码前缀: 'MISSING' |
| `SOT-005` | `backend/routers/daily_reports.py:891` | 无效的错误码前缀: 'MISSING' |
| `SOT-005` | `backend/routers/daily_reports.py:1029` | 无效的错误码前缀: 'NO' |
| `SOT-005` | `backend/routers/daily_reports.py:1031` | 无效的错误码前缀: 'NO' |
| `SOT-005` | `backend/routers/daily_reports.py:1149` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1151` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1209` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1211` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1293` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1295` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1344` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1346` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1415` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1417` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1482` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1484` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1510` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/daily_reports.py:1512` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/topup.py:144` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/topup.py:146` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/topup.py:632` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/topup.py:634` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/topup.py:656` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/topup.py:658` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/topup.py:721` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/topup.py:723` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/transfers.py:137` | 无效的错误码前缀: 'VALIDATION' |
| `SOT-005` | `backend/routers/transfers.py:84` | 无效的错误码前缀: 'INTERNAL' |
| `SOT-005` | `backend/routers/transfers.py:131` | 无效的错误码前缀: 'OPERATION' |

## 警告

| 代码 | 文件:行 | 描述 |
|------|---------|------|
| `INT-003` | `backend/services/daily_report_service.py:17` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/daily_report_service.py:17` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/daily_report_service.py:17` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/daily_report_service.py:17` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/daily_report_service.py:17` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/daily_report_service.py:18` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/daily_report_service.py:18` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/daily_report_service.py:19` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/daily_report_service.py:19` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/topup_service.py:15` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/topup_service.py:15` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/topup_service.py:15` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/topup_service.py:16` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/topup_service.py:16` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/topup_service.py:16` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/topup_service.py:16` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/topup_service.py:16` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/transfer_service.py:20` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/transfer_service.py:20` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/transfer_service.py:20` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/transfer_service.py:21` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/transfer_service.py:22` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/transfer_service.py:22` | 第三方库未安装: sqlalchemy |
| `SOT-006` | `backend/services/ledger_service.py:283` | 直接返回 dict，未使用标准响应格式 |
| `SOT-006` | `backend/services/ledger_service.py:406` | 直接返回 dict，未使用标准响应格式 |
| `SOT-006` | `backend/services/ledger_service.py:542` | 直接返回 dict，未使用标准响应格式 |
| `INT-003` | `backend/services/ledger_service.py:50` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/ledger_service.py:51` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/ledger_service.py:51` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/ledger_service.py:51` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/services/ledger_service.py:51` | 第三方库未安装: sqlalchemy |
| `SOT-004` | `backend/routers/daily_reports.py:453` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:455` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:493` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:495` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:539` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:541` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:582` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:584` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:625` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:627` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:668` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:670` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:711` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:713` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:842` | 错误码格式不正确: 'INVALID-FILE-TYPE' |
| `SOT-004` | `backend/routers/daily_reports.py:844` | 错误码格式不正确: 'INVALID-FILE-TYPE' |
| `SOT-004` | `backend/routers/daily_reports.py:856` | 错误码格式不正确: 'FILE-TOO-LARGE' |
| `SOT-004` | `backend/routers/daily_reports.py:858` | 错误码格式不正确: 'FILE-TOO-LARGE' |
| `SOT-004` | `backend/routers/daily_reports.py:869` | 错误码格式不正确: 'EXCEL-PARSE-ERROR' |
| `SOT-004` | `backend/routers/daily_reports.py:871` | 错误码格式不正确: 'EXCEL-PARSE-ERROR' |
| `SOT-004` | `backend/routers/daily_reports.py:1013` | 错误码格式不正确: 'EXPORT-LIMIT-EXCEEDED' |
| `SOT-004` | `backend/routers/daily_reports.py:1018` | 错误码格式不正确: 'EXPORT-LIMIT-EXCEEDED' |
| `SOT-004` | `backend/routers/daily_reports.py:1196` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:1198` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:1337` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/daily_reports.py:1339` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `INT-003` | `backend/routers/daily_reports.py:12` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/daily_reports.py:12` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/daily_reports.py:12` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/daily_reports.py:12` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/daily_reports.py:12` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/daily_reports.py:12` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/daily_reports.py:12` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/daily_reports.py:13` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/daily_reports.py:14` | 第三方库未安装: sqlalchemy |
| `INT-003` | `backend/routers/daily_reports.py:16` | 第三方库未安装: pandas |
| `SOT-004` | `backend/routers/topup.py:215` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/topup.py:261` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/topup.py:307` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/topup.py:353` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/topup.py:399` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/topup.py:452` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/topup.py:505` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/topup.py:559` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/topup.py:596` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/topup.py:681` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `INT-003` | `backend/routers/topup.py:10` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/topup.py:10` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/topup.py:10` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/topup.py:10` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/topup.py:10` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/topup.py:10` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/topup.py:11` | 第三方库未安装: sqlalchemy |
| `SOT-004` | `backend/routers/transfers.py:125` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/transfers.py:162` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/transfers.py:195` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/transfers.py:241` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/transfers.py:287` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `SOT-004` | `backend/routers/transfers.py:333` | 错误码格式不正确: 'RESOURCE-NOT-FOUND' |
| `INT-003` | `backend/routers/transfers.py:14` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/transfers.py:14` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/transfers.py:14` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/transfers.py:14` | 第三方库未安装: fastapi |
| `INT-003` | `backend/routers/transfers.py:15` | 第三方库未安装: sqlalchemy |

## 文件详情

- :x: `backend/services/daily_report_service.py` - 问题: 11, 修复: 0
- :x: `backend/services/topup_service.py` - 问题: 46, 修复: 0
- :x: `backend/services/transfer_service.py` - 问题: 17, 修复: 0
- :white_check_mark: `backend/services/ledger_service.py` - 问题: 8, 修复: 0
- :x: `backend/routers/daily_reports.py` - 问题: 85, 修复: 0
- :x: `backend/routers/topup.py` - 问题: 25, 修复: 0
- :x: `backend/routers/transfers.py` - 问题: 14, 修复: 0