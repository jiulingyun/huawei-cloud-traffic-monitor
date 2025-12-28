#!/bin/bash

echo "======================================"
echo "  环境验证脚本"
echo "======================================"
echo ""

# 检查 Python 版本
echo "1. 检查 Python 版本..."
python3 --version
if [ $? -eq 0 ]; then
    echo "✅ Python 已安装"
else
    echo "❌ Python 未安装"
    exit 1
fi
echo ""

# 检查 Node.js 版本
echo "2. 检查 Node.js 版本..."
node --version
if [ $? -eq 0 ]; then
    echo "✅ Node.js 已安装"
else
    echo "❌ Node.js 未安装"
    exit 1
fi
echo ""

# 检查后端虚拟环境
echo "3. 检查 Python 虚拟环境..."
if [ -d "backend/venv" ]; then
    echo "✅ Python 虚拟环境已创建"
else
    echo "❌ Python 虚拟环境未创建"
    exit 1
fi
echo ""

# 检查后端依赖
echo "4. 检查后端依赖..."
if backend/venv/bin/pip show fastapi > /dev/null 2>&1; then
    echo "✅ FastAPI 已安装"
else
    echo "❌ FastAPI 未安装"
    exit 1
fi

if backend/venv/bin/pip show uvicorn > /dev/null 2>&1; then
    echo "✅ Uvicorn 已安装"
else
    echo "❌ Uvicorn 未安装"
    exit 1
fi

if backend/venv/bin/pip show sqlalchemy > /dev/null 2>&1; then
    echo "✅ SQLAlchemy 已安装"
else
    echo "❌ SQLAlchemy 未安装"
    exit 1
fi

if backend/venv/bin/pip show apscheduler > /dev/null 2>&1; then
    echo "✅ APScheduler 已安装"
else
    echo "❌ APScheduler 未安装"
    exit 1
fi
echo ""

# 检查前端依赖
echo "5. 检查前端依赖..."
if [ -d "frontend/node_modules" ]; then
    echo "✅ 前端依赖已安装"
else
    echo "❌ 前端依赖未安装"
    exit 1
fi

if [ -d "frontend/node_modules/vue" ]; then
    echo "✅ Vue 3 已安装"
else
    echo "❌ Vue 3 未安装"
    exit 1
fi

if [ -d "frontend/node_modules/element-plus" ]; then
    echo "✅ Element Plus 已安装"
else
    echo "❌ Element Plus 未安装"
    exit 1
fi

if [ -d "frontend/node_modules/vite" ]; then
    echo "✅ Vite 已安装"
else
    echo "❌ Vite 未安装"
    exit 1
fi
echo ""

echo "======================================"
echo "  ✅ 环境验证通过！"
echo "======================================"
echo ""
echo "可以开始开发了："
echo "  后端: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  前端: cd frontend && npm run dev"
