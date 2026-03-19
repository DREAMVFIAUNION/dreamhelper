'use client'

const TECH_STACK = [
  { name: 'MiniMax', logo: '🧠' },
  { name: 'Qwen-3', logo: '🧠' },
  { name: 'GLM-4.7', logo: '🧠' },
  { name: 'Next.js', logo: '▲' },
  { name: 'FastAPI', logo: '⚡' },
  { name: 'n8n', logo: '⚙️' },
  { name: 'PostgreSQL', logo: '🐘' },
  { name: 'Redis', logo: '◆' },
]

function TechItem({ name, logo }: { name: string; logo: string }) {
  return (
    <div className="flex items-center gap-3 text-muted-foreground/70 hover:text-primary/80
                     transition-colors duration-300 cursor-default px-8 shrink-0">
      <span className="text-lg">{logo}</span>
      <span className="text-xs font-mono tracking-wider whitespace-nowrap">{name}</span>
    </div>
  )
}

export function TrustBar() {
  // 4x duplication for seamless fill on any viewport
  const items = [...TECH_STACK, ...TECH_STACK, ...TECH_STACK, ...TECH_STACK]

  return (
    <section className="py-12 border-b border-border overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <p className="text-center text-xs font-mono text-muted-foreground tracking-[0.3em] mb-8">
          POWERED BY
        </p>
      </div>
      <div className="relative group">
        {/* Fade edges */}
        <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none" />
        <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none" />

        <div
          className="flex items-center will-change-transform animate-[marquee_30s_linear_infinite] group-hover:[animation-play-state:paused]"
          style={{ width: 'max-content' }}
        >
          {items.map(({ name, logo }, i) => (
            <TechItem key={`${name}-${i}`} name={name} logo={logo} />
          ))}
        </div>
      </div>

      <style jsx>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-25%); }
        }
      `}</style>
    </section>
  )
}
