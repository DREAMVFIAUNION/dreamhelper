// ═══ 邮件发送 lib ═══
// 优先级: Resend API → SMTP (nodemailer) → 控制台输出 (dev)

import { sendEmail as resendSend, hasResendConfig } from '@/lib/email/resend'

interface SendMailOptions {
  to: string
  subject: string
  html: string
}

const SMTP_HOST = process.env.SMTP_HOST ?? ''
const SMTP_PORT = process.env.SMTP_PORT ?? '587'
const SMTP_USER = process.env.SMTP_USER ?? ''
const SMTP_PASS = process.env.SMTP_PASS ?? ''
const SMTP_FROM = process.env.SMTP_FROM ?? 'noreply@dreamvfia.com'

function hasSmtpConfig(): boolean {
  return !!(SMTP_HOST && SMTP_USER && SMTP_PASS)
}

/**
 * 发送邮件
 * 1. 有 RESEND_API_KEY: 使用 Resend API 发送
 * 2. 有 SMTP 配置: 使用 nodemailer 发送
 * 3. 均无: 控制台输出 (开发模式)
 */
export async function sendMail(options: SendMailOptions): Promise<{ sent: boolean; devFallback: boolean }> {
  // === 优先使用 Resend ===
  if (hasResendConfig()) {
    const result = await resendSend({ to: options.to, subject: options.subject, html: options.html })
    if (result.success) {
      return { sent: true, devFallback: false }
    }
    console.error('[email] Resend failed, trying SMTP fallback:', result.error)
  }

  // === SMTP fallback ===
  if (hasSmtpConfig()) {
    try {
      // 动态 require nodemailer（可选依赖，未安装时 fallback 到控制台）
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const nm = require('nodemailer') as {
        createTransport: (opts: Record<string, unknown>) => {
          sendMail: (msg: Record<string, string>) => Promise<void>
        }
      }
      const transporter = nm.createTransport({
        host: SMTP_HOST,
        port: Number(SMTP_PORT),
        secure: Number(SMTP_PORT) === 465,
        auth: { user: SMTP_USER, pass: SMTP_PASS },
      })

      await transporter.sendMail({
        from: SMTP_FROM,
        to: options.to,
        subject: options.subject,
        html: options.html,
      })

      return { sent: true, devFallback: false }
    } catch (error) {
      console.error('[email] SMTP send failed:', error)
    }
  }

  // === 开发模式降级: 控制台输出 ===
  console.log('═══════════════════════════════════════')
  console.log(`[EMAIL DEV] To: ${options.to}`)
  console.log(`[EMAIL DEV] Subject: ${options.subject}`)
  console.log(`[EMAIL DEV] Body:\n${options.html.replace(/<[^>]+>/g, '')}`)
  console.log('═══════════════════════════════════════')

  return { sent: false, devFallback: true }
}

function escapeHtml(str: string): string {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

/** 发送邮箱验证码 */
export async function sendVerificationEmail(
  to: string,
  code: string,
): Promise<{ sent: boolean; devFallback: boolean }> {
  return sendMail({
    to,
    subject: '【DREAMVFIA】邮箱验证码',
    html: `
      <div style="font-family: monospace; background: #0a0a14; color: #e0e0e0; padding: 32px; max-width: 480px; margin: 0 auto;">
        <h2 style="color: #fe0000; letter-spacing: 0.1em;">DREAMVFIA · 邮箱验证</h2>
        <p>您的验证码为：</p>
        <div style="font-size: 32px; font-weight: bold; color: #fe0000; letter-spacing: 0.3em; padding: 16px 0; text-align: center; background: #1a1a2e; border: 1px solid #fe000040; margin: 16px 0;">
          ${escapeHtml(code)}
        </div>
        <p style="color: #888; font-size: 12px;">验证码 10 分钟内有效，请勿将此验证码告诉他人。</p>
        <hr style="border-color: #333; margin: 24px 0;" />
        <p style="color: #555; font-size: 10px;">此邮件由系统自动发送，请勿回复。</p>
      </div>
    `,
  })
}

/** 发送密码重置链接 */
export async function sendPasswordResetEmail(
  to: string,
  resetUrl: string,
): Promise<{ sent: boolean; devFallback: boolean }> {
  return sendMail({
    to,
    subject: '【DREAMVFIA】密码重置',
    html: `
      <div style="font-family: monospace; background: #0a0a14; color: #e0e0e0; padding: 32px; max-width: 480px; margin: 0 auto;">
        <h2 style="color: #fe0000; letter-spacing: 0.1em;">DREAMVFIA · 密码重置</h2>
        <p>您正在申请重置密码，请点击以下链接：</p>
        <a href="${escapeHtml(resetUrl)}" style="display: block; padding: 12px 24px; background: #fe0000; color: #000; font-weight: bold; text-align: center; text-decoration: none; letter-spacing: 0.1em; margin: 16px 0;">
          重置密码
        </a>
        <p style="color: #888; font-size: 12px;">链接 30 分钟内有效。如果您没有申请重置密码，请忽略此邮件。</p>
        <hr style="border-color: #333; margin: 24px 0;" />
        <p style="color: #555; font-size: 10px;">此邮件由系统自动发送，请勿回复。</p>
      </div>
    `,
  })
}
