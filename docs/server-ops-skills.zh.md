# 服务端运维技能（server_ops）

## 启用步骤

1. 管理后台 → **系统设置** → **安全** → 打开 **服务端运维技能**
2. **技能管理** → **重新加载**（同步 `skills/mchat-ops`）
3. 使用**管理员账号**在管理后台 **对话**（不要通过 Widget/门户通道）

## 内置技能 `mchat-ops`

| command | 说明 |
|---------|------|
| health | 进程内 DB / Milvus / Redis 状态（不 HTTP 自调，避免单 worker 死锁） |
| logs | 尾部 `logs/app.log` 或 `error.log` |
| milvus | Milvus 启用状态与连接 |
| k8s | 只读 `kubectl get pods|nodes|...`（需服务器已配置 kubectl） |
| redis | Redis Ping |
| disk | 磁盘用量 |
| services | `systemctl is-active`（mchat-cloud-backend 等） |
| db | MySQL `SELECT 1` |
| run | 执行 **系统设置 → 安全 → 运维 Shell 白名单** 中的命令（`shell_id`） |

### Shell 白名单格式

每行：`命令id | 完整命令`（按空格分词执行，**不用** shell；禁止 `;`、`|`、`&&` 等）。

```
k8s-pods | kubectl get pods -n default -o wide --request-timeout=30s
k8s-nodes | kubectl get nodes -o wide
```

对话示例：`用 mchat-ops 执行 run，shell_id 为 k8s-pods`

重新加载技能时 API 会返回 `server_ops` 技能名列表（默认禁用，需手动启用）。

## 安全策略

- `SKILL.md` 中 `scope: server_ops` 的技能受全局开关约束
- 绑定 **CustomerConfig** 的通道（Widget、门户等）**不会**加载运维技能
- 通道/模板保存时会**自动剔除** `server_ops` 技能 ID
- 仅 `user.role == admin` 且开关开启时生效（且无 CustomerConfig 的对话）
- 可选白名单：设置里逗号分隔技能名，留空表示允许全部 `server_ops` 技能
- **维护模式**：系统设置开启后，Widget/门户/支付等对外 API 返回 503，管理员仍可登录后台运维

## 从磁盘同步

`server_ops` 技能首次同步时默认 **禁用**，需在技能列表手动启用后再打开系统开关。

## 新增运维技能

在 `skills/` 下新建目录，`SKILL.md` 增加：

```yaml
scope: server_ops
requires_admin: true
```

并实现 `main.py` 的 `run(**kwargs)` 入口。
