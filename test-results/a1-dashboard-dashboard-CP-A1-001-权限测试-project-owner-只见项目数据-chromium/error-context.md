# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - generic [ref=e4]:
      - heading "AI 广告代投系统" [level=2] [ref=e5]
      - paragraph [ref=e6]: 请登录您的账户
    - generic [ref=e7]:
      - generic [ref=e8]:
        - generic [ref=e9]:
          - generic [ref=e10]: 用户名或邮箱
          - textbox "用户名或邮箱" [ref=e11]: owner@test.local
        - generic [ref=e12]:
          - generic [ref=e13]: 密码
          - textbox "密码" [ref=e14]: test123
        - generic [ref=e15]:
          - generic [ref=e16]:
            - checkbox "记住我" [ref=e17]
            - generic [ref=e18]: 记住我
          - link "忘记密码？" [ref=e19] [cursor=pointer]:
            - /url: /forgot-password
      - button "登录" [ref=e21] [cursor=pointer]
      - generic [ref=e22]:
        - text: 还没有账户？
        - link "立即注册" [ref=e23] [cursor=pointer]:
          - /url: /register
  - region "Notifications alt+T":
    - list:
      - listitem [ref=e24]:
        - img [ref=e26]
        - generic [ref=e29]: Internal Server Error
  - button "Open Next.js Dev Tools" [ref=e35] [cursor=pointer]:
    - img [ref=e36]
  - alert [ref=e39]
```