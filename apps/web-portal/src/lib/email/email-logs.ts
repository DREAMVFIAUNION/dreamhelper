// ═══ 邮件发送日志（内存存储，重启后清空）═══

export interface EmailLog {
  id: string
  subject: string
  recipientCount: number
  sent: number
  failed: number
  sentAt: string
}

const emailLogs: EmailLog[] = []

export function addEmailLog(opts: { subject: string; recipientCount: number; sent: number; failed: number }) {
  emailLogs.unshift({
    id: `log_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    subject: opts.subject,
    recipientCount: opts.recipientCount,
    sent: opts.sent,
    failed: opts.failed,
    sentAt: new Date().toISOString(),
  })
  // 只保留最近 100 条
  if (emailLogs.length > 100) emailLogs.length = 100
}

export function getEmailLogs(): EmailLog[] {
  return emailLogs
}
