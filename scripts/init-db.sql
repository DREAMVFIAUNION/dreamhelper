-- 初始化多数据库：dreamhelp (主应用) + n8n (工作流引擎)
-- 此脚本在 PostgreSQL 容器首次启动时自动执行

-- n8n 工作流引擎数据库（主数据库 dreamhelp 由 POSTGRES_DB 环境变量自动创建）
SELECT 'CREATE DATABASE n8n'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'n8n')\gexec

-- 授权 dreamhelp 用户访问 n8n 数据库
GRANT ALL PRIVILEGES ON DATABASE n8n TO dreamhelp;
