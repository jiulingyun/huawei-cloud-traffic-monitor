# 用户认证与登录

## 概述

本系统实现了基于 JWT (JSON Web Token) 的用户认证机制。由于这是一个单用户监控系统，采用了简化的认证方案，管理员账户通过环境变量配置。

## 技术方案

### 后端实现

#### 1. JWT 认证
- **库**: python-jose[cryptography]
- **算法**: HS256
- **Token 有效期**: 24小时（1440分钟）
- **密钥配置**: 通过环境变量 `JWT_SECRET_KEY` 配置

#### 2. 管理员账户
- **配置方式**: 环境变量
- **默认账户**: 
  - 用户名: `admin`
  - 密码: `admin123`
- **生产环境**: 务必修改 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 环境变量

#### 3. API 端点

**POST /v1/auth/login**
- 描述: 用户登录
- 请求体:
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```
- 响应:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "username": "admin",
    "expires_in": 86400
  }
  ```

**POST /v1/auth/logout**
- 描述: 用户登出
- 说明: 简化版本，实际由前端清除token

**GET /v1/auth/me**
- 描述: 获取当前用户信息
- 响应:
  ```json
  {
    "username": "admin",
    "role": "admin"
  }
  ```

### 前端实现

#### 1. 登录页面
- **路径**: `/login`
- **功能**:
  - 用户名/密码表单
  - 表单验证（用户名2-50字符，密码≥6字符）
  - 加载状态显示
  - 错误提示
  - 回车键登录
  - 默认账户提示

#### 2. 会话管理

**User Store (Pinia)**
- **状态**:
  - `token`: JWT访问令牌
  - `userInfo`: 用户信息对象
  - `isLoggedIn`: 登录状态（计算属性）

- **方法**:
  - `setToken(token)`: 保存token到store和localStorage
  - `setUserInfo(info)`: 保存用户信息
  - `logout()`: 清除token和用户信息

**持久化**:
- Token和用户信息存储在 `localStorage`
- 页面刷新后自动恢复登录状态

#### 3. 路由守卫

**认证检查** (`router/index.js`):
```javascript
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    // 需要认证但未登录 → 跳转登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && userStore.isLoggedIn) {
    // 已登录访问登录页 → 跳转首页
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})
```

#### 4. HTTP 拦截器

**请求拦截器** (`utils/request.js`):
```javascript
request.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

**响应拦截器**:
```javascript
request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // 未授权 → 清除token并跳转登录
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

## 使用流程

### 1. 登录流程
```
用户输入账号密码
    ↓
前端表单验证
    ↓
调用 POST /v1/auth/login
    ↓
后端验证用户名密码
    ↓
生成 JWT token
    ↓
前端保存 token 和用户信息
    ↓
跳转到目标页面或首页
```

### 2. 认证访问流程
```
用户访问需要认证的页面
    ↓
路由守卫检查登录状态
    ↓
已登录？
  ├─ 是 → 继续访问
  └─ 否 → 跳转登录页
```

### 3. API 请求流程
```
前端发起API请求
    ↓
请求拦截器自动添加 Authorization header
    ↓
后端接收请求
    ↓
验证 token（如需要）
    ↓
返回响应
    ↓
响应拦截器处理
```

### 4. 登出流程
```
用户点击退出登录
    ↓
调用 POST /v1/auth/logout (可选)
    ↓
清除本地 token 和用户信息
    ↓
跳转登录页
```

## 环境配置

### 开发环境

**.env (后端)**:
```bash
JWT_SECRET_KEY=dev-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 生产环境

**强烈建议修改以下配置**:

1. **JWT密钥**: 生成强随机密钥
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **管理员账户**: 修改默认用户名和密码
   ```bash
   ADMIN_USERNAME=your_admin_username
   ADMIN_PASSWORD=your_strong_password_here
   ```

## 安全考虑

### 已实现
✅ JWT token 认证  
✅ 密码环境变量配置  
✅ Token 自动过期（24小时）  
✅ 401 自动跳转登录  
✅ HTTPS（生产环境建议）  

### 未来改进
- [ ] 密码哈希存储（如使用数据库）
- [ ] Token 刷新机制
- [ ] 多用户支持
- [ ] 角色权限控制
- [ ] 登录日志记录
- [ ] 防暴力破解（登录限流）

## 故障排查

### 登录失败
1. 检查用户名密码是否正确
2. 查看浏览器控制台错误信息
3. 检查后端 API 是否正常运行
4. 验证环境变量配置

### Token 过期
- Token 有效期为 24小时
- 过期后需要重新登录
- 前端会自动检测 401 并跳转登录页

### 401 错误
- 检查 token 是否存在于 localStorage
- 验证 token 是否正确添加到请求头
- 确认 token 未过期

## API 测试

### cURL 示例

**登录**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**获取用户信息**:
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 参考资料

- [JWT.io](https://jwt.io/)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
- [Vue Router Navigation Guards](https://router.vuejs.org/guide/advanced/navigation-guards.html)
- [Axios Interceptors](https://axios-http.com/docs/interceptors)
