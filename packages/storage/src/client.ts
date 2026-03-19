import { Client } from 'minio'
import { Readable } from 'stream'
import crypto from 'crypto'

export interface StorageConfig {
  endPoint: string
  port: number
  useSSL: boolean
  accessKey: string
  secretKey: string
  defaultBucket: string
}

export interface UploadResult {
  bucket: string
  key: string
  url: string
  size: number
  contentType: string
  etag: string
}

const DEFAULT_CONFIG: StorageConfig = {
  endPoint: process.env.MINIO_ENDPOINT?.split(':')[0] || 'localhost',
  port: parseInt(process.env.MINIO_ENDPOINT?.split(':')[1] || '9000'),
  useSSL: false,
  accessKey: process.env.MINIO_ACCESS_KEY || 'minioadmin',
  secretKey: process.env.MINIO_SECRET_KEY || 'minioadmin',
  defaultBucket: process.env.MINIO_BUCKET || 'dreamhelp',
}

let _instance: StorageClient | null = null

export function getStorageClient(config?: Partial<StorageConfig>): StorageClient {
  if (!_instance) {
    _instance = new StorageClient({ ...DEFAULT_CONFIG, ...config })
  }
  return _instance
}

export class StorageClient {
  private client: Client
  private bucket: string

  constructor(config: StorageConfig = DEFAULT_CONFIG) {
    this.client = new Client({
      endPoint: config.endPoint,
      port: config.port,
      useSSL: config.useSSL,
      accessKey: config.accessKey,
      secretKey: config.secretKey,
    })
    this.bucket = config.defaultBucket
  }

  /** 确保 bucket 存在 */
  async ensureBucket(bucket?: string): Promise<void> {
    const b = bucket || this.bucket
    const exists = await this.client.bucketExists(b)
    if (!exists) {
      await this.client.makeBucket(b)
      console.log(`[Storage] Created bucket: ${b}`)
    }
  }

  /** 上传 Buffer */
  async upload(
    buffer: Buffer,
    options: {
      filename: string
      contentType?: string
      bucket?: string
      prefix?: string
    },
  ): Promise<UploadResult> {
    const bucket = options.bucket || this.bucket
    await this.ensureBucket(bucket)

    const ext = options.filename.split('.').pop() || ''
    const hash = crypto.createHash('md5').update(buffer).digest('hex').slice(0, 8)
    const timestamp = Date.now()
    const prefix = options.prefix || 'uploads'
    const key = `${prefix}/${timestamp}-${hash}.${ext}`

    const contentType = options.contentType || getMimeType(ext)

    const stream = Readable.from(buffer)
    const result = await this.client.putObject(bucket, key, stream, buffer.length, {
      'Content-Type': contentType,
      'X-Original-Filename': encodeURIComponent(options.filename),
    })

    return {
      bucket,
      key,
      url: `/${bucket}/${key}`,
      size: buffer.length,
      contentType,
      etag: result.etag,
    }
  }

  /** 获取文件流 */
  async getObject(key: string, bucket?: string): Promise<Readable> {
    return this.client.getObject(bucket || this.bucket, key)
  }

  /** 删除文件 */
  async deleteObject(key: string, bucket?: string): Promise<void> {
    await this.client.removeObject(bucket || this.bucket, key)
  }

  /** 生成预签名 URL（有效期默认 1 小时） */
  async getPresignedUrl(key: string, expirySeconds = 3600, bucket?: string): Promise<string> {
    return this.client.presignedGetObject(bucket || this.bucket, key, expirySeconds)
  }

  /** 获取文件信息 */
  async statObject(key: string, bucket?: string) {
    return this.client.statObject(bucket || this.bucket, key)
  }
}

function getMimeType(ext: string): string {
  const mimeMap: Record<string, string> = {
    pdf: 'application/pdf',
    txt: 'text/plain',
    md: 'text/markdown',
    json: 'application/json',
    csv: 'text/csv',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    png: 'image/png',
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    gif: 'image/gif',
    svg: 'image/svg+xml',
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
    mp4: 'video/mp4',
    zip: 'application/zip',
  }
  return mimeMap[ext.toLowerCase()] || 'application/octet-stream'
}
