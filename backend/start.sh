#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 启动 FastAPI 服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
