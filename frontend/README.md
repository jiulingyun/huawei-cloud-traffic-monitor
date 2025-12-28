# 前端应用

基于 Vue.js 3 + Vite + Element Plus 的华为云流量监控前端应用。

## 技术栈

- Vue.js 3 - 渐进式框架
- Vite - 现代化构建工具
- Vue Router - 路由管理
- Pinia - 状态管理
- Element Plus - UI 组件库
- Axios - HTTP 客户端

## 开发环境

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── assets/          # 静态资源
│   ├── components/      # 通用组件
│   ├── views/           # 页面视图
│   ├── router/          # 路由配置
│   ├── store/           # 状态管理
│   ├── api/             # API 接口
│   ├── styles/          # 全局样式
│   ├── utils/           # 工具函数
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── index.html           # HTML 模板
├── vite.config.js       # Vite 配置
└── package.json         # 依赖配置
```

## 代理配置

开发环境已配置 API 代理，前端请求 `/api/*` 会自动转发到后端服务 `http://localhost:8000`。
