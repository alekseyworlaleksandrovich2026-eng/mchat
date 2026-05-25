# MinIO / S3 存储测试

在管理后台 **系统设置** 中配置：

- `storage_backend`: `minio` 或 `s3`
- `s3_endpoint`: 例如 `http://10.98.8.12:9000`
- `s3_access_key` / `s3_secret_key`
- `s3_bucket`: 桶名（需已创建）
- `s3_force_path_style`: `true`（MinIO 一般为 true）
- `s3_public_base_url`（可选）: 对外访问前缀

保存后重启后端：`systemctl --user restart mchat-cloud-backend`

## 命令行快速验证

在服务器上（已配置 `.env` 或管理端写入的 settings）：

```bash
cd /opt/xiaoxiao/mchat/src/backend
source venv/bin/activate
python - <<'PY'
from app.core.config import settings
from app.services.storage_service import StorageService

svc = StorageService()
url = svc.save(b"minio-test", key="healthchecks/minio.txt", content_type="text/plain")
print("OK:", url)
PY
```

成功会打印 `OK:` 加 URL。

## 业务侧验证

1. 管理端上传知识库文件或对话附件
2. 检查 MinIO 控制台对应 bucket 是否出现对象
3. 若配置了 `s3_public_base_url`，在浏览器打开返回的 URL 应能访问

## 常见问题

- **403 / AccessDenied**: 检查 AK/SK 与 bucket 策略
- **连接失败**: `s3_endpoint` 是否可从 10.98.8.15 访问（防火墙、端口）
- **本地仍写 uploads/**: `storage_backend` 未生效，需重启服务并确认 settings 已持久化
