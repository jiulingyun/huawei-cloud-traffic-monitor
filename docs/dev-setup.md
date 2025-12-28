# 开发环境配置指南

本文档介绍如何配置华为云服务器流量监控系统的开发环境。

## 环境要求

- Python 3.9+
- Node.js 18+
- Git

## 后端环境配置

### 1. 创建 Python 虚拟环境

```bash
cd backend
python3 -m venv venv
```

### 2. 激活虚拟环境

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，根据实际情况配置
```

### 5. 启动后端服务

```bash
# 方式 1: 使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式 2: 使用启动脚本
./start.sh

# 方式 3: 直接运行
python -m app.main
```

访问 API 文档:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 前端环境配置

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产版本

```bash
npm run preview
```

## 环境验证

运行环境验证脚本，确认所有依赖已正确安装：

```bash
# 从项目根目录运行
./scripts/verify-env.sh
```

验证通过后，你将看到：

```
======================================
  ✅ 环境验证通过！
======================================

可以开始开发了：
  后端: cd backend && source venv/bin/activate && uvicorn app.main:app --reload
  前端: cd frontend && npm run dev
```

## 常见问题

### Python 虚拟环境激活失败

**问题**: 虚拟环境激活后命令行没有变化

**解决**: 确认 Python 3 已正确安装，重新创建虚拟环境

### 依赖安装失败

**问题**: pip 安装依赖时出现网络错误

**解决**: 
1. 检查网络连接
2. 使用国内镜像源：
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### 前端依赖安装慢

**问题**: npm install 速度很慢

**解决**: 使用国内镜像：
```bash
npm install --registry=https://registry.npmmirror.com
```

### 端口占用

**问题**: 后端或前端服务启动失败，提示端口被占用

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8000  # 后端
lsof -i :5173  # 前端

# 杀死进程
kill -9 <PID>
```

## IDE 配置建议

### VS Code

推荐安装以下扩展：
- Python
- Pylance
- Vue Language Features (Volar)
- ESLint
- Prettier

### PyCharm

1. 配置 Python 解释器为虚拟环境中的 Python
2. 启用 FastAPI 支持

## 开发工作流

1. 启动后端服务（终端 1）
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. 启动前端服务（终端 2）
   ```bash
   cd frontend
   npm run dev
   ```

3. 开始开发，修改代码后：
   - 后端会自动重载（--reload 参数）
   - 前端会自动热更新（Vite HMR）

## 下一步

环境配置完成后，可以继续：
- 阅读 [项目架构文档](./architecture.md)
- 查看 [开发规范](../.warp/project-rules.md)
- 开始认领开发任务
