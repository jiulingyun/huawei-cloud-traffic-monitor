# 华为云服务器流量监控与自动关机系统

一个支持多账户的华为云服务器流量监控系统，能够实时监控服务器流量包剩余量，当流量低于用户设置的阈值时自动关机，并通过飞书发送通知。

## 项目简介

本系统旨在帮助华为云用户：
- 实时监控多个账户下的服务器流量使用情况
- 自动关闭流量即将耗尽的服务器，避免超额费用
- 通过飞书及时接收监控告警和关机通知
- 提供友好的 Web 管理界面，便于配置和管理

## 主要功能

- ✅ **多账户管理**：支持添加和管理多个华为云账户
- ✅ **实时监控**：定时监控服务器流量包剩余量
- ✅ **智能告警**：流量低于阈值时触发告警
- ✅ **自动关机**：自动关闭流量不足的服务器
- ✅ **飞书通知**：通过飞书 Webhook 发送实时通知
- ✅ **Web 管理界面**：直观的管理控制台
- ✅ **加密存储**：安全存储账户凭证信息

## 技术栈

### 后端
- Python 3.10+
- FastAPI - 高性能 Web 框架
- SQLite - 轻量级数据库
- APScheduler - 任务调度
- Requests - HTTP 客户端

### 前端
- Vue.js 3 - 渐进式前端框架
- Vite - 现代化构建工具
- Element Plus - UI 组件库
- Axios - HTTP 客户端

## 项目结构

```
huawei-cloud-traffic-monitor/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心功能
│   │   ├── models/      # 数据模型
│   │   ├── services/    # 业务逻辑
│   │   └── utils/       # 工具函数
│   ├── tests/           # 测试
│   └── requirements.txt # 依赖列表
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # 组件
│   │   ├── views/       # 页面
│   │   ├── router/      # 路由
│   │   ├── store/       # 状态管理
│   │   └── api/         # API 调用
│   └── package.json     # 依赖列表
├── docker/              # Docker 配置
├── docs/                # 文档
└── README.md            # 项目说明
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- SQLite 3

### 后端安装

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 前端安装

```bash
cd frontend
npm install
```

### 运行

```bash
# 后端
cd backend
uvicorn app.main:app --reload

# 前端
cd frontend
npm run dev
```

## 配置说明

### 华为云账户配置

1. 在华为云控制台创建 AK/SK
2. 在系统中添加账户信息
3. 系统将自动加密存储凭证

### 飞书 Webhook 配置

1. 在飞书群组中创建自定义机器人
2. 获取 Webhook URL
3. 在系统中配置通知地址

### 监控配置

- 设置流量阈值（GB）
- 配置监控频率（分钟）
- 启用/禁用自动关机

## 部署

### Docker 部署

```bash
docker-compose up -d
```

### 手动部署

详见 [部署文档](docs/deployment.md)

## 开发指南

本项目使用 DevGenius 进行任务管理和开发协作。

### 开发流程

1. 查看当前任务列表
2. 认领任务并更新状态
3. 遵循代码规范进行开发
4. 编写测试并验证功能
5. 提交代码并更新文档

详见 [开发规则](.warp/project-rules.md)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。

---

**开发状态**：🚧 开发中

**当前版本**：v0.1.0-alpha
