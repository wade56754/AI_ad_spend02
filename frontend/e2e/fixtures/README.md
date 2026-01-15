# E2E 测试固定资源

该目录包含 E2E 测试所需的固定资源文件，如测试图片、文档等。

## 文件列表

### 图片文件

- `test-proof.jpg` - 用于充值凭证上传测试的示例图片
- `test-avatar.png` - 用于用户头像上传测试的示例图片
- `large-image.jpg` - 用于测试大文件上传的图片（> 5MB）

### 文档文件

- `test-report.xlsx` - 用于日报批量导入测试的 Excel 文件
- `test-reconciliation.csv` - 用于对账导入测试的 CSV 文件

## 使用方法

在测试中引用这些文件：

```typescript
import * as path from 'path';

const testFilePath = path.join(__dirname, '../../fixtures/test-proof.jpg');
await topupPage.uploadProof(testFilePath);
```

## 文件要求

### 充值凭证图片要求

- 格式: JPG, PNG
- 大小: < 5MB
- 尺寸: 建议 800x600 或更大

### 日报 Excel 要求

- 格式: XLSX
- 必需列: 日期、账号、消耗、转化等
- 示例数据: 至少 5-10 行

### 对账 CSV 要求

- 格式: CSV (UTF-8)
- 必需列: 交易ID、金额、时间等
- 示例数据: 至少 5-10 行

## 注意事项

1. 所有测试文件应该是真实但无敏感信息的示例数据
2. 图片文件应该压缩以减小仓库大小
3. 不要上传真实的用户数据或凭证
4. 定期检查文件是否损坏或过期

## 生成测试文件

如果测试文件不存在，可以使用以下脚本生成：

```bash
# 生成测试图片
pnpm run generate:test-images

# 生成测试 Excel
pnpm run generate:test-excel

# 生成测试 CSV
pnpm run generate:test-csv
```
