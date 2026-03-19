// ═══ Resend 邮件发送封装 ═══
import { Resend } from 'resend'

const RESEND_API_KEY = process.env.RESEND_API_KEY ?? ''
const RESEND_FROM = process.env.RESEND_FROM ?? 'DREAMVFIA <onboarding@resend.dev>'

let _resend: Resend | null = null

function getResend(): Resend | null {
  if (!RESEND_API_KEY) return null
  if (!_resend) _resend = new Resend(RESEND_API_KEY)
  return _resend
}

export function hasResendConfig(): boolean {
  return !!RESEND_API_KEY
}

export interface SendResult {
  success: boolean
  id?: string
  error?: string
}

/** 发送单封邮件 */
export async function sendEmail(options: {
  to: string | string[]
  subject: string
  html: string
  from?: string
}): Promise<SendResult> {
  const resend = getResend()
  if (!resend) {
    return { success: false, error: 'RESEND_API_KEY 未配置' }
  }

  try {
    const { data, error } = await resend.emails.send({
      from: options.from ?? RESEND_FROM,
      to: Array.isArray(options.to) ? options.to : [options.to],
      subject: options.subject,
      html: options.html,
    })

    if (error) {
      console.error('[resend] send failed:', error)
      return { success: false, error: error.message }
    }

    return { success: true, id: data?.id }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error('[resend] exception:', msg)
    return { success: false, error: msg }
  }
}

/** 批量发送（Resend Batch API，一次最多 100 封） */
export async function sendBatchEmails(options: {
  recipients: string[]
  subject: string
  html: string
  from?: string
}): Promise<{ total: number; sent: number; failed: number; errors: string[] }> {
  const resend = getResend()
  if (!resend) {
    return { total: 0, sent: 0, failed: 0, errors: ['RESEND_API_KEY 未配置'] }
  }

  const from = options.from ?? RESEND_FROM
  const BATCH_SIZE = 50
  const errors: string[] = []
  let sent = 0
  let failed = 0

  // Resend batch API: send individually for reliability
  for (let i = 0; i < options.recipients.length; i += BATCH_SIZE) {
    const batch = options.recipients.slice(i, i + BATCH_SIZE)
    const promises = batch.map(async (to) => {
      const result = await sendEmail({ to, subject: options.subject, html: options.html, from })
      if (result.success) {
        sent++
      } else {
        failed++
        errors.push(`${to}: ${result.error}`)
      }
    })
    await Promise.all(promises)
  }

  return { total: options.recipients.length, sent, failed, errors }
}
