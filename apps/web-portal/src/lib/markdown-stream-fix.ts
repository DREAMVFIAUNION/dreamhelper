/**
 * 修复流式 Markdown 中间状态
 *
 * 流式输出时 Markdown 是逐字到达的，中间状态可能出现：
 * - 未闭合的代码块 ``` 导致整个页面变成代码
 * - 未闭合的加粗 ** 导致后续文本全部加粗
 * - LaTeX 公式 $$ 未闭合导致渲染错误
 *
 * 此函数在渲染前对未闭合的标记进行补全。
 */
export function fixStreamingMarkdown(text: string): string {
  if (!text) return text
  let fixed = text

  // 1. 修复未闭合的代码块 ```
  const codeBlockCount = (fixed.match(/```/g) || []).length
  if (codeBlockCount % 2 !== 0) {
    fixed += '\n```'
  }

  // 2. 修复未闭合的行内代码 `
  //    先排除 ``` 中的 `，再计数剩余的单独 `
  const withoutTriple = fixed.replace(/```[\s\S]*?```/g, '')
  const inlineCodeCount = (withoutTriple.match(/(?<!`)`(?!`)/g) || []).length
  if (inlineCodeCount % 2 !== 0) {
    fixed += '`'
  }

  // 3. 修复未闭合的加粗 **
  const boldCount = (fixed.match(/\*\*/g) || []).length
  if (boldCount % 2 !== 0) {
    fixed += '**'
  }

  // 4. 修复未闭合的斜体 * (排除 ** 中的 *)
  const stripped = fixed.replace(/\*\*/g, '')
  const italicCount = (stripped.match(/\*/g) || []).length
  if (italicCount % 2 !== 0) {
    fixed += '*'
  }

  // 5. 修复未闭合的删除线 ~~
  const strikeCount = (fixed.match(/~~/g) || []).length
  if (strikeCount % 2 !== 0) {
    fixed += '~~'
  }

  // 6. 修复未闭合的 LaTeX 块级公式 $$
  const blockLatexCount = (fixed.match(/\$\$/g) || []).length
  if (blockLatexCount % 2 !== 0) {
    fixed += '$$'
  }

  // 7. 修复未闭合的 LaTeX 行内公式 $ (排除 $$ 中的 $)
  const strippedBlock = fixed.replace(/\$\$/g, '')
  const inlineLatexCount = (strippedBlock.match(/\$/g) || []).length
  if (inlineLatexCount % 2 !== 0) {
    fixed += '$'
  }

  return fixed
}
