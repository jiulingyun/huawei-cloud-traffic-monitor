# 数据库设计文档

本文档描述华为云服务器流量监控系统的数据库结构设计。

## 数据库类型

SQLite 3

## 表结构

### 1. accounts - 账户表

存储华为云账户信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键ID | PRIMARY KEY |
| name | VARCHAR(100) | 账户名称 | NOT NULL |
| ak | VARCHAR(255) | Access Key（加密存储） | NOT NULL |
| sk | VARCHAR(255) | Secret Key（加密存储） | NOT NULL |
| region | VARCHAR(50) | 华为云区域 | NOT NULL, DEFAULT 'cn-north-4' |
| is_enabled | BOOLEAN | 是否启用 | DEFAULT TRUE |
| description | VARCHAR(500) | 账户描述 | |
| created_at | DATETIME | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | DEFAULT CURRENT_TIMESTAMP |

**说明**：
- AK/SK 需要加密存储，确保安全性
- 支持多个账户管理
- 可通过 is_enabled 字段启用/禁用账户

### 2. servers - 服务器表

存储服务器信息及流量数据。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键ID | PRIMARY KEY |
| account_id | INTEGER | 所属账户ID | NOT NULL, FOREIGN KEY |
| server_id | VARCHAR(100) | 华为云服务器ID | NOT NULL, UNIQUE |
| name | VARCHAR(200) | 服务器名称 | NOT NULL |
| ip_address | VARCHAR(50) | IP地址 | |
| status | VARCHAR(50) | 服务器状态 | |
| traffic_total | FLOAT | 总流量包大小（GB） | |
| traffic_remaining | FLOAT | 剩余流量（GB） | |
| traffic_used | FLOAT | 已用流量（GB） | |
| last_check_time | DATETIME | 最后检查时间 | |
| created_at | DATETIME | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | DEFAULT CURRENT_TIMESTAMP |

**说明**：
- server_id 为华为云返回的唯一服务器标识
- 流量信息会定期更新
- 级联删除：删除账户时自动删除关联服务器

### 3. configs - 配置表

存储监控配置信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键ID | PRIMARY KEY |
| account_id | INTEGER | 关联账户ID | FOREIGN KEY (NULL=全局配置) |
| check_interval | INTEGER | 检查间隔（分钟） | DEFAULT 5 |
| traffic_threshold | FLOAT | 流量阈值（GB） | DEFAULT 10.0 |
| auto_shutdown_enabled | BOOLEAN | 是否启用自动关机 | DEFAULT TRUE |
| feishu_webhook_url | VARCHAR(500) | 飞书 Webhook URL（加密） | |
| notification_enabled | BOOLEAN | 是否启用通知 | DEFAULT TRUE |
| shutdown_delay | INTEGER | 关机延迟（分钟） | DEFAULT 0 |
| retry_times | INTEGER | 失败重试次数 | DEFAULT 3 |
| created_at | DATETIME | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | DEFAULT CURRENT_TIMESTAMP |

**说明**：
- account_id 为 NULL 表示全局配置
- 账户级配置优先于全局配置
- Webhook URL 需要加密存储

### 4. monitor_logs - 监控日志表

记录每次流量监控的结果。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键ID | PRIMARY KEY |
| account_id | INTEGER | 账户ID | NOT NULL, FOREIGN KEY |
| server_id | INTEGER | 服务器ID | NOT NULL, FOREIGN KEY |
| traffic_remaining | FLOAT | 剩余流量（GB） | NOT NULL |
| traffic_total | FLOAT | 总流量（GB） | |
| traffic_used | FLOAT | 已用流量（GB） | |
| usage_percentage | FLOAT | 使用百分比 | |
| threshold | FLOAT | 当时的阈值（GB） | NOT NULL |
| is_below_threshold | BOOLEAN | 是否低于阈值 | DEFAULT FALSE |
| check_time | DATETIME | 检查时间 | DEFAULT CURRENT_TIMESTAMP |
| message | VARCHAR(500) | 日志消息 | |
| created_at | DATETIME | 创建时间 | DEFAULT CURRENT_TIMESTAMP |

**说明**：
- 记录每次监控的详细信息
- 便于追溯和统计分析
- 建议定期清理历史数据

### 5. shutdown_logs - 关机日志表

记录服务器关机操作。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键ID | PRIMARY KEY |
| account_id | INTEGER | 账户ID | NOT NULL, FOREIGN KEY |
| server_id | INTEGER | 服务器ID | NOT NULL, FOREIGN KEY |
| reason | VARCHAR(200) | 关机原因 | NOT NULL |
| status | VARCHAR(50) | 关机状态 | NOT NULL |
| job_id | VARCHAR(100) | 华为云任务ID | |
| traffic_remaining | VARCHAR(50) | 关机时剩余流量 | |
| error_message | TEXT | 错误信息 | |
| shutdown_time | DATETIME | 实际关机时间 | |
| created_at | DATETIME | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | DEFAULT CURRENT_TIMESTAMP |

**说明**：
- status 可能的值：pending（等待中）、success（成功）、failed（失败）
- job_id 用于跟踪华为云异步任务状态
- 记录关机操作的完整信息，便于审计

### 6. notification_logs - 通知日志表

记录飞书通知发送记录。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键ID | PRIMARY KEY |
| notification_type | VARCHAR(50) | 通知类型 | NOT NULL |
| title | VARCHAR(200) | 通知标题 | |
| content | TEXT | 通知内容 | NOT NULL |
| status | VARCHAR(50) | 发送状态 | NOT NULL |
| webhook_url | VARCHAR(500) | Webhook URL（脱敏） | |
| response_code | INTEGER | HTTP 响应状态码 | |
| error_message | TEXT | 错误信息 | |
| retry_count | INTEGER | 重试次数 | DEFAULT 0 |
| created_at | DATETIME | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | DEFAULT CURRENT_TIMESTAMP |

**说明**：
- notification_type 可能的值：alert（告警）、shutdown（关机通知）、error（错误通知）
- status 可能的值：pending（等待中）、success（成功）、failed（失败）
- webhook_url 仅存储脱敏版本（隐藏敏感信息）

## ER 关系图

```
┌──────────┐         ┌──────────┐
│ accounts │◄────┬───│ servers  │
└──────────┘     │   └──────────┘
      ▲          │        ▲
      │          │        │
      │          │        │
┌─────┴────┐     │   ┌────┴──────────┐
│ configs  │     │   │ monitor_logs  │
└──────────┘     │   └───────────────┘
                 │        ▲
                 │        │
                 │   ┌────┴──────────┐
                 └───│ shutdown_logs │
                     └───────────────┘
```

## 关系说明

- 一个账户（Account）可以有多个服务器（Server） - 1:N
- 一个账户（Account）可以有多个配置（Config） - 1:N
- 一个服务器（Server）会产生多条监控日志（MonitorLog） - 1:N
- 一个服务器（Server）会产生多条关机日志（ShutdownLog） - 1:N
- 通知日志（NotificationLog）独立存储，不关联其他表

## 索引设计

### 主键索引
所有表的 `id` 字段都自动创建主键索引。

### 外键索引
- servers.account_id
- configs.account_id
- monitor_logs.account_id
- monitor_logs.server_id
- shutdown_logs.account_id
- shutdown_logs.server_id

### 唯一索引
- servers.server_id (UNIQUE) - 确保华为云服务器ID唯一

### 建议的查询索引
- monitor_logs.check_time - 便于按时间查询监控记录
- monitor_logs.is_below_threshold - 便于快速查询告警记录
- shutdown_logs.status - 便于按状态查询关机记录
- notification_logs.status - 便于按状态查询通知记录

## 数据安全

### 加密字段
以下字段需要加密存储：
- accounts.ak（Access Key）
- accounts.sk（Secret Key）
- configs.feishu_webhook_url（飞书 Webhook URL）

### 脱敏字段
以下字段存储时需要脱敏：
- notification_logs.webhook_url（仅存储域名部分，隐藏完整 URL）

## 初始化

### 创建数据库

```bash
cd backend
python init_db.py
```

### 验证表结构

```bash
sqlite3 data/monitor.db ".schema"
```

## 数据维护

### 定期清理建议
- monitor_logs: 保留最近 30 天的记录
- notification_logs: 保留最近 30 天的记录
- shutdown_logs: 建议永久保留，用于审计

### 备份策略
建议每天备份 SQLite 数据库文件：
```bash
cp data/monitor.db data/monitor_backup_$(date +%Y%m%d).db
```
