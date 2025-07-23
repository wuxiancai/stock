-- 初始化数据库脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建索引优化查询性能
-- 这些索引将在 Alembic 迁移中创建，这里仅作为参考

-- 插入系统配置数据
INSERT INTO system_config (key, value, description, is_active) VALUES
('system.version', '1.0.0', '系统版本号', true),
('system.maintenance_mode', 'false', '维护模式开关', true),
('data.update_interval', '300', '数据更新间隔（秒）', true),
('cache.default_ttl', '3600', '默认缓存过期时间（秒）', true),
('api.rate_limit', '1000', 'API 速率限制（每分钟请求数）', true),
('websocket.max_connections', '1000', 'WebSocket 最大连接数', true),
('task.retry_times', '3', '任务重试次数', true),
('log.retention_days', '30', '日志保留天数', true)
ON CONFLICT (key) DO NOTHING;