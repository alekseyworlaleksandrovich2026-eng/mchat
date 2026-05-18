#!/bin/bash
# mchat 一键部署脚本
# 用法: bash ops/scripts/deploy.sh [dev|prod]

set -euo pipefail

MODE="${1:-dev}"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "🚀 mchat 部署脚本"
echo "模式: $MODE"
echo "项目目录: $PROJECT_DIR"

cd "$PROJECT_DIR"

case "$MODE" in
  dev)
    echo ""
    echo "📦 启动开发环境..."
    echo ""

    # 检查 .env 文件
    if [ ! -f ops/docker/.env ]; then
      echo "⚠️  未找到 ops/docker/.env，从模板创建..."
      cp ops/docker/.env.example ops/docker/.env
      echo "✅ 请编辑 ops/docker/.env 配置环境变量后重新运行"
      exit 1
    fi

    # 构建并启动
    docker compose -f ops/docker/docker-compose.yml build
    docker compose -f ops/docker/docker-compose.yml up -d

    echo ""
    echo "✅ 开发环境启动成功！"
    echo ""
    echo "访问地址:"
    echo "  管理后台: http://localhost:5173/admin"
    echo "  API 文档: http://localhost:3001/docs"
    echo "  健康检查: http://localhost:3001/api/health"
    echo ""
    echo "查看日志: docker compose -f ops/docker/docker-compose.yml logs -f"
    ;;

  prod)
    echo ""
    echo "📦 启动生产环境..."

    if [ ! -f ops/docker/.env.production ]; then
      echo "❌ 未找到 ops/docker/.env.production"
      echo "请从 ops/docker/.env.example 创建并配置生产环境变量"
      exit 1
    fi

    docker compose -f ops/docker/docker-compose.prod.yml --env-file ops/docker/.env.production build
    docker compose -f ops/docker/docker-compose.prod.yml --env-file ops/docker/.env.production up -d

    echo ""
    echo "✅ 生产环境启动成功！"
    ;;

  stop)
    echo "🛑 停止服务..."
    docker compose -f ops/docker/docker-compose.yml down
    docker compose -f ops/docker/docker-compose.prod.yml down 2>/dev/null || true
    echo "✅ 服务已停止"
    ;;

  *)
    echo "用法: bash deploy.sh [dev|prod|stop]"
    exit 1
    ;;
esac
