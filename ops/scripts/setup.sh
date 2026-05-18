#!/bin/bash
# mchat 开发环境快速设置脚本
# 用于在新机器上快速搭建开发环境

set -euo pipefail

echo "🔧 mchat 开发环境设置"

# 检查依赖
check_command() {
  if ! command -v "$1" &> /dev/null; then
    echo "❌ 缺少依赖: $1"
    echo "   请先安装 $1"
    exit 1
  fi
}

echo ""
echo "检查依赖..."
check_command python3
check_command node
check_command npm
check_command docker

# Python 版本检查
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION"
echo "✅ Node $(node -v)"
echo "✅ npm $(npm -v)"
echo "✅ Docker $(docker -v)"

# 创建 .env
echo ""
echo "📝 配置环境变量..."
if [ ! -f src/backend/.env ]; then
  cp src/backend/.env.example src/backend/.env
  echo "✅ 已创建 src/backend/.env（请根据需要修改）"
else
  echo "⏭️  src/backend/.env 已存在，跳过"
fi

if [ ! -f ops/docker/.env ]; then
  cp ops/docker/.env.example ops/docker/.env
  echo "✅ 已创建 ops/docker/.env（请根据需要修改）"
else
  echo "⏭️  ops/docker/.env 已存在，跳过"
fi

# 启动开发数据库
echo ""
echo "🗄️  启动开发数据库..."
docker compose -f ops/docker/docker-compose.dev.yml up -d mysql

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
for i in $(seq 1 30); do
  if docker exec mchat-dev-mysql mysqladmin ping -h localhost -u root -pdev_password --silent 2>/dev/null; then
    echo "✅ 数据库已就绪"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "⚠️  数据库启动超时，请手动检查"
  fi
  sleep 2
done

# 安装 Python 依赖
echo ""
echo "📦 安装 Python 依赖..."
cd src/backend
if [ ! -d venv ]; then
  python3 -m venv venv
  echo "✅ 已创建虚拟环境"
fi
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库表
echo ""
echo "🗃️  初始化数据库表..."
python -c "
from app.core.database import engine, Base
from app.models import *
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ 数据库表创建完成')

asyncio.run(init_db())
"

# 安装前端依赖
echo ""
echo "📦 安装前端依赖..."
cd ../frontend
npm install

echo ""
echo "============================================"
echo "✅ 开发环境设置完成！"
echo ""
echo "启动开发服务器:"
echo "  终端1: cd src/backend && source venv/bin/activate && uvicorn app.main:app --reload --port 3001"
echo "  终端2: cd src/frontend && npm run dev"
echo ""
echo "访问:"
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:3001"
echo "  API文档: http://localhost:3001/docs"
echo "============================================"
