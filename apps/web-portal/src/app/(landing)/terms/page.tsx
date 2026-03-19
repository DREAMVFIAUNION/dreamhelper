'use client'

import { motion } from 'framer-motion'

const SECTIONS = [
  {
    title: '1. 服务描述',
    content: `梦帮小助是由 DREAMVFIA 提供的 AI 智能助手平台，包括但不限于：

- AI 对话服务（三脑并行架构）
- 知识库管理与 RAG 检索
- 智能体与技能系统
- 多渠道接入（Web、微信、企微、Telegram）
- 语音交互（TTS/STT）

我们保留随时修改、暂停或终止部分功能的权利，并会提前通知用户。`,
  },
  {
    title: '2. 账户注册与管理',
    content: `- 您须年满 16 周岁方可注册使用本服务。
- 注册信息应真实、准确、完整，并及时更新。
- 每位用户仅限注册一个账户，不得转让或借用。
- 您有责任妥善保管账户密码，因密码泄露导致的损失由您自行承担。
- 我们有权在发现违规行为时暂停或注销您的账户。`,
  },
  {
    title: '3. 使用规范',
    content: `使用梦帮小助服务时，您同意不会：

- 利用服务生成违反法律法规、公序良俗的内容
- 发布或传播恶意软件、垃圾信息
- 尝试攻击、入侵、逆向工程或干扰服务运行
- 以自动化方式过度调用 API（超出套餐限制）
- 冒充他人或虚假陈述与任何人或实体的关系
- 上传侵犯他人知识产权的内容到知识库
- 利用 AI 输出进行欺诈、诽谤或其他非法活动`,
  },
  {
    title: '4. 知识产权',
    content: `- 梦帮小助平台的软件、界面、商标、Logo 等知识产权归 DREAMVFIA 所有。
- 您上传到知识库的文档内容，知识产权仍归您或原始权利人所有。
- AI 生成的回复内容供您个人或商业使用，但我们不对其准确性作保证。
- 您授予我们处理您上传内容的必要许可，仅限于提供服务所需。`,
  },
  {
    title: '5. 套餐与付费',
    content: `- 免费版：每日 5,000 Token，基础功能。
- 专业版：¥29.9/月（年付 ¥299），50 万 Token/月，全部技能。
- 企业版：¥99.9/月（年付 ¥999），200 万 Token/月，团队协作。

付费套餐自购买之日起生效。退款政策：购买后 7 天内未使用可申请全额退款。
Token 额度按自然月重置，未使用部分不结转。`,
  },
  {
    title: '6. 免责声明',
    content: `- AI 生成的内容仅供参考，不构成专业建议（包括但不限于法律、医疗、财务建议）。
- 我们不保证服务 100% 不间断或无错误，但承诺 99.9% 的可用率目标。
- 因不可抗力（如自然灾害、网络攻击、政策变化）导致的服务中断，我们不承担责任。
- 第三方 AI 模型提供商的服务变更可能影响部分功能，我们会尽力提供替代方案。`,
  },
  {
    title: '7. 隐私保护',
    content: `我们重视您的隐私。有关个人信息收集、使用和保护的详细说明，请参阅我们的《隐私政策》。`,
  },
  {
    title: '8. 协议变更',
    content: `我们可能根据法律法规变化或业务需要修改本协议。重大变更将提前 15 天通过站内通知或邮件告知。
变更生效后继续使用服务即视为接受新协议。如不同意变更，您有权注销账户。`,
  },
  {
    title: '9. 争议解决',
    content: `- 本协议适用中华人民共和国法律。
- 因本协议引起的争议，双方应友好协商解决。
- 协商不成的，任何一方可向 DREAMVFIA 所在地有管辖权的人民法院提起诉讼。`,
  },
]

export default function TermsPage() {
  return (
    <div className="pt-24 pb-20">
      <div className="max-w-4xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">TERMS OF SERVICE</p>
          <h1 className="text-3xl md:text-5xl font-display font-bold">用户协议</h1>
          <p className="mt-4 text-sm text-muted-foreground">最后更新：2026 年 2 月 26 日</p>
          <div className="mt-4 mx-auto w-20 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <p className="text-sm text-muted-foreground leading-relaxed mb-8">
            欢迎使用梦帮小助！本用户协议（以下简称"协议"）是您与 DREAMVFIA（以下简称"我们"）之间关于使用梦帮小助 AI 助手服务的法律协议。
            注册或使用本服务即表示您已阅读、理解并同意受本协议约束。
          </p>

          <div className="space-y-6">
            {SECTIONS.map((s, i) => (
              <motion.div
                key={s.title}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.08 * i }}
                className="p-6 bg-card border border-border rounded-lg"
              >
                <h2 className="text-base font-bold mb-3">{s.title}</h2>
                <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                  {s.content.split(/\*\*([^*]+)\*\*/).map((part, j) =>
                    j % 2 === 1 ? <strong key={j} className="text-foreground">{part}</strong> : <span key={j}>{part}</span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
