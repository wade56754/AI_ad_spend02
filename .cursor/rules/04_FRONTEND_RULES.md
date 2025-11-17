# 前端强制规则

必用：apiFetch (位于 /lib/api.ts)
禁止：fetch() / axios() / createClient()
请求演示：
```ts
const res = await apiFetch("/api/v1/daily-reports", {
  method: "POST",
  body: {...}
});
