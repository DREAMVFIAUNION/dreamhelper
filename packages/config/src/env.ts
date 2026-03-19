import { z } from 'zod'

export const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'staging', 'production']).default('development'),
  LOG_LEVEL: z.enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace']).default('info'),

  // Database
  DATABASE_URL: z.string().url(),
  DATABASE_READ_URL: z.string().url().optional(),

  // Redis
  REDIS_URL: z.string().url(),

  // Milvus
  MILVUS_HOST: z.string().default('localhost'),
  MILVUS_PORT: z.coerce.number().default(19530),

  // Elasticsearch
  ELASTICSEARCH_URL: z.string().url().default('http://localhost:9200'),

  // MinIO
  MINIO_ENDPOINT: z.string().default('localhost:9000'),
  MINIO_ACCESS_KEY: z.string(),
  MINIO_SECRET_KEY: z.string(),

  // LLM
  MINIMAX_API_KEY: z.string().optional(),
  MINIMAX_GROUP_ID: z.string().optional(),
  OPENAI_API_KEY: z.string().optional(),

  // JWT
  JWT_SECRET: z.string().min(16),
  JWT_EXPIRES_IN: z.string().default('7d'),
})

export type EnvConfig = z.infer<typeof envSchema>
