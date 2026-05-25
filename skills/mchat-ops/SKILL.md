---
name: mchat-ops
description: 服务端运维巡检（健康检查、日志、Milvus、只读 K8s）。仅管理员且在系统设置中启用后可用。
type: tool
scope: server_ops
requires_admin: true
parameters: {"type":"object","properties":{"command":{"type":"string","enum":["health","logs","milvus","k8s","redis","disk"]},"source":{"type":"string","enum":["app","error"]},"lines":{"type":"integer"},"namespace":{"type":"string"},"resource":{"type":"string","enum":["pods","nodes","deployments","services","events"]}},"required":["command"]}
---

# MChat 服务端运维

在**管理后台对话**（非 Widget/门户通道）中，由管理员启用的运维工具。

## 子命令

- `health` — 本机 `/api/health` 与数据库探测摘要
- `logs` — 尾部日志（`source`: app | error，`lines`: 默认 80）
- `milvus` — Milvus 运行时配置与连接状态
- `k8s` — 只读 `kubectl get`（需服务器安装 kubectl 且配置 kubeconfig）
- `redis` — Ping Redis（`REDIS_URL`）
- `disk` — 磁盘用量摘要

## 安全

禁止删除/应用资源；门户与 Widget 通道不会加载本技能。
