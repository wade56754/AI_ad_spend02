# 前端规则（React / Next.js）

📌 API 调用必须执行以下标准：
- 使用封装函数：apiFetch
- 不允许使用 fetch、axios、request、createClient
- API 返回值必须解析 Envelope

示例（正确）：
```ts
import { apiFetch } from "@/lib/api";

const res = await apiFetch("/api/v1/projects", {
  method: "GET",
});
