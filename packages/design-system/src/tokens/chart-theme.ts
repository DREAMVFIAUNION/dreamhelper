/**
 * 梦帮小助 · 图表配色方案（Recharts / ECharts）
 */

export const chartTheme = {
  axisLine: { stroke: '#2A2A2A' },
  axisLabel: { fill: '#606060', fontFamily: 'JetBrains Mono', fontSize: 10 },
  gridLine: { stroke: '#1E1E1E', strokeDasharray: '3 3' },

  series: [
    '#FE0000', // 品牌红
    '#00BFFF', // 赛博蓝
    '#00FF88', // 赛博绿
    '#FFB800', // 琥珀
    '#FF6B6B', // 浅红
    '#8B5CF6', // 紫色
  ],

  tooltip: {
    backgroundColor: '#141414',
    borderColor: '#FE000040',
    textColor: '#F0F0F0',
    fontFamily: 'JetBrains Mono',
    fontSize: 11,
  },

  legend: {
    textColor: '#A0A0A0',
    fontFamily: 'JetBrains Mono',
    fontSize: 11,
  },
} as const
