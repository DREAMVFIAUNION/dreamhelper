'use client'

import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { animate, stagger } from 'animejs'
import { ShinyText } from './effects/ShinyText'

const CATEGORIES = [
  { key: 'daily',   label: '日常', emoji: '🌟', count: 15 },
  { key: 'office',  label: '办公', emoji: '💼', count: 15 },
  { key: 'doc',     label: '文档', emoji: '📄', count: 13 },
  { key: 'image',   label: '图像', emoji: '🖼️', count: 12 },
  { key: 'audio',   label: '音频', emoji: '🎵', count: 10 },
  { key: 'video',   label: '视频', emoji: '🎬', count: 8 },
  { key: 'coding',  label: '编程', emoji: '💻', count: 16 },
  { key: 'fun',     label: '娱乐', emoji: '🎮', count: 12 },
]

const SKILLS: Record<string, string[]> = {
  daily:  ['计算器', '单位换算', '日期计算', '密码生成', 'BMI 计算', '农历转换', '星座查询', '倒计时', '随机选择器', '摩斯电码', '色彩转换', '进制转换', '温度换算', '汇率估算', '时区转换'],
  office: ['待办管理', '番茄钟', '会议纪要', 'CSV 分析', 'JSON 格式化', '记账本', '看板管理', '日程规划', '邮件模板', '周报生成', '思维导图', '甘特图', '发票计算', '工时统计', '项目估算'],
  doc:    ['Markdown 处理', '文本统计', '正则构建', 'PDF 读取', 'Word 读取', '文档加密', '文本对比', '批量重命名', '模板填充', '目录生成', '格式转换', '文本翻译', '摘要提取'],
  image:  ['图片缩放', '图片裁剪', '图片旋转', '添加水印', '图片压缩', '格式转换', '滤镜效果', '二维码生成', '二维码识别', 'EXIF 读取', '拼图合成', '颜色提取'],
  audio:  ['音频信息', '格式转换', '音频裁剪', '音频合并', '音量调节', '音频分割', '变速播放', '静音检测', '波形生成', '音频元数据'],
  video:  ['视频信息', '视频截图', '视频裁剪', '视频合并', '转 GIF', '提取音频', '视频压缩', '帧率调整'],
  coding: ['Base64 编解码', 'URL 编解码', '哈希计算', 'UUID 生成', 'JWT 解码', 'IP 计算', '文件哈希', '正则测试', 'SQL 格式化', 'JSON 校验', 'HTML 实体', 'ENV 解析', '代码格式化', '代码压缩', 'Diff 补丁', '正则测试器'],
  fun:    ['骰子', '硬币翻转', '今日运势', '姓名生成', 'Lorem Ipsum', 'ASCII 艺术', '数字趣闻', 'Emoji 艺术', '迷宫生成', '数独求解', '字谜游戏', '石头剪刀布'],
}

export function SkillsShowcase() {
  const [active, setActive] = useState('daily')
  const gridRef = useRef<HTMLDivElement>(null)

  const animateGrid = useCallback(() => {
    if (!gridRef.current) return
    const items = gridRef.current.querySelectorAll('[data-skill-item]')
    if (items.length === 0) return
    animate(items, {
      opacity: [0, 1],
      scale: [0.85, 1],
      translateY: ['15px', '0px'],
      duration: 400,
      delay: stagger(30, { from: 'first' }),
      ease: 'easeOutQuint',
    })
  }, [])

  return (
    <section className="py-24 border-t border-border">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">SKILL CORE SYSTEM</p>
          <h2 className="text-3xl md:text-4xl font-display font-bold">
            <ShinyText text="100 个核心技能" speed={4} color="hsl(var(--foreground))" />
          </h2>
          <p className="mt-3 text-sm text-muted-foreground font-mono">零 API 依赖 · 离线可用 · 一键调用</p>
        </motion.div>

        {/* 分类标签 */}
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {CATEGORIES.map(({ key, label, emoji, count }) => (
            <button
              key={key}
              onClick={() => setActive(key)}
              className={`
                px-4 py-2 text-sm font-mono transition-all duration-200
                [clip-path:polygon(4px_0%,100%_0%,100%_calc(100%-4px),calc(100%-4px)_100%,0%_100%,0%_4px)]
                ${active === key
                  ? 'bg-primary text-primary-foreground font-bold shadow-[0_0_15px_hsl(var(--primary)/0.2)]'
                  : 'bg-secondary text-muted-foreground border border-border hover:border-primary/30 hover:text-foreground'}
              `}
            >
              {emoji} {label} ({count})
            </button>
          ))}
        </div>

        {/* 技能网格 */}
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            ref={gridRef}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onAnimationComplete={animateGrid}
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3"
          >
            {SKILLS[active]?.map((skill) => (
              <div
                key={skill}
                data-skill-item
                className="
                  group px-4 py-3 text-center text-sm font-mono
                  bg-card/80 border border-border
                  hover:border-primary/40 hover:bg-primary/10
                  transition-all duration-200 cursor-default
                  [clip-path:polygon(4px_0%,100%_0%,100%_calc(100%-4px),calc(100%-4px)_100%,0%_100%,0%_4px)]
                "
                style={{ opacity: 0 }}
              >
                <span className="text-muted-foreground/90 group-hover:text-primary transition-colors">{skill}</span>
              </div>
            ))}
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  )
}
