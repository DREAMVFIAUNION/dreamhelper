'use client'

import { motion } from 'framer-motion'
import { Mail, MapPin, ExternalLink } from 'lucide-react'

const SOCIAL_GROUPS = [
  {
    title: '视频平台',
    links: [
      { name: 'YouTube · DREAMVFIA', url: 'https://www.youtube.com/@DREAMVFIA' },
      { name: 'YouTube · RNOISE RECORDS', url: 'https://www.youtube.com/@RNOISERECORDS' },
      { name: 'YouTube · S.R BEATZ', url: 'https://www.youtube.com/@S.RBEATZ_DREAMVFIA' },
      { name: 'YouTube · QMYTH404', url: 'https://www.youtube.com/@QMYTH404_DREAMVFIA' },
      { name: 'YouTube · SEANPILOT', url: 'https://www.youtube.com/@SEANPILOT_DREAMVFIA' },
      { name: 'B站', url: 'https://space.bilibili.com/3546688251759455' },
    ],
  },
  {
    title: '社交媒体',
    links: [
      { name: 'Facebook', url: 'https://www.facebook.com/profile.php?id=61584667876802' },
      { name: 'Instagram', url: 'https://www.instagram.com/rnoise_official/' },
      { name: 'X · RNOISE RECORDS', url: 'https://x.com/RNOISERECORDS' },
      { name: 'X · DREAMVFIA UNION', url: 'https://x.com/dreamvfiaunion' },
      { name: '微博 · RNOISE唱片', url: 'https://weibo.com/u/4095511237' },
      { name: '微博 · 梦帮集团', url: 'https://weibo.com/u/7916708062' },
      { name: 'Pinterest · DREAMVFIA', url: 'https://www.pinterest.com/DREAMVFIA_UNION/' },
      { name: 'Pinterest · RNOISE', url: 'https://www.pinterest.com/rnoiserecords/' },
      { name: 'WhatsApp Channel', url: 'https://whatsapp.com/channel/0029VbBWLNzFCCoNMSLBIG10' },
    ],
  },
  {
    title: '社区 & 博客',
    links: [
      { name: 'Discord', url: 'https://discord.gg/avXdpScxJp' },
      { name: 'CSDN 博客', url: 'https://dreamvfia.blog.csdn.net' },
      { name: '百度百家号', url: 'https://author.baidu.com/home?from=bjh_article&app_id=1788007741352242' },
    ],
  },
  {
    title: '音乐平台 · Spotify',
    links: [
      { name: 'S.R BEATZ', url: 'https://open.spotify.com/artist/1fCtgWSvwomeSLmrFddcPT' },
      { name: 'QMYTH404', url: 'https://open.spotify.com/artist/7v5ORPukAn7nPs7IZBPUSr' },
      { name: 'SEANPILOT', url: 'https://open.spotify.com/artist/5PcOEWESTygHsdCyavWXNf' },
    ],
  },
  {
    title: '音乐平台 · QQ音乐',
    links: [
      { name: 'S.R BEATZ', url: 'https://y.qq.com/n/ryqq_v2/singer/0044CsFf1AkGkJ' },
      { name: 'QMYTH404', url: 'https://y.qq.com/n/ryqq_v2/singer/0018THEr2QnYhtV' },
      { name: 'SEANPILOT', url: 'https://y.qq.com/n/ryqq_v2/singer/000P1bEY0q0Om9' },
    ],
  },
  {
    title: '音乐平台 · 网易云',
    links: [
      { name: 'S.R BEATZ', url: 'https://music.163.com/#/artist?id=13037777' },
      { name: 'QMYTH404', url: 'https://music.163.com/#/artist?id=35219595' },
      { name: 'SEANPILOT', url: 'https://music.163.com/#/artist?id=61573307' },
    ],
  },
]

export default function ContactPage() {
  return (
    <div className="pt-24 pb-20">
      <div className="max-w-5xl mx-auto px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">CONTACT US</p>
          <h1 className="text-3xl md:text-5xl font-display font-bold">联系我们</h1>
          <div className="mt-4 mx-auto w-20 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        {/* Contact Info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16"
        >
          <div className="p-6 bg-card border border-border rounded-lg flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Mail size={18} className="text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-mono font-bold mb-1">邮箱</h3>
              <p className="text-sm text-muted-foreground">support@dreamvfia.com</p>
              <p className="text-sm text-muted-foreground">business@dreamvfia.com</p>
            </div>
          </div>
          <div className="p-6 bg-card border border-border rounded-lg flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <MapPin size={18} className="text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-mono font-bold mb-1">总部</h3>
              <p className="text-sm text-muted-foreground">DREAMVFIA CORP.</p>
              <p className="text-sm text-muted-foreground">梦帮集团</p>
            </div>
          </div>
        </motion.div>

        {/* Social Links */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <h2 className="text-xl font-display font-bold mb-2">全网社交平台</h2>
          <p className="text-sm text-muted-foreground mb-8">关注我们，获取最新动态</p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {SOCIAL_GROUPS.map((group) => (
              <div key={group.title} className="p-5 bg-card border border-border rounded-lg">
                <h3 className="text-xs font-mono text-primary tracking-wider mb-4 font-bold">
                  {group.title}
                </h3>
                <ul className="space-y-2.5">
                  {group.links.map((link) => (
                    <li key={link.url}>
                      <a
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors group"
                      >
                        <ExternalLink size={12} className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                        <span className="truncate">{link.name}</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
