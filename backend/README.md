# 后端服务

基于 FastAPI 的华为云流量监控后端服务。

## 技术栈

- Python 3.10+
- FastAPI - Web 框架
- SQLAlchemy - ORM
- APScheduler - 任务调度
- SQLite - 数据库

## 开发环境

### 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置相关参数
```

### 运行服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Python 直接运行
python -m app.main
```

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # 应用入口
│   ├── api/             # API 路由
│   ├── core/            # 核心配置
│   ├── models/          # 数据模型
│   ├── services/        # 业务逻辑
│   └── utils/           # 工具函数
├── tests/               # 测试
├── requirements.txt     # 依赖列表
└── .env.example         # 环境变量示例
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

```bash
pytest
```
