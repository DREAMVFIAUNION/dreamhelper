'use client'

import { Component, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex flex-col items-center justify-center min-h-[300px] p-8">
          <AlertTriangle size={32} className="text-primary mb-4" />
          <h2 className="text-sm font-mono font-bold text-foreground mb-2">页面出现错误</h2>
          <p className="text-[10px] font-mono text-muted-foreground mb-4 max-w-sm text-center">
            {this.state.error?.message || '发生了未知错误'}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: undefined })
              window.location.reload()
            }}
            className="flex items-center gap-1.5 px-4 py-2 bg-primary text-primary-foreground font-mono font-bold text-xs rounded-md hover:bg-primary/90 transition-colors"
          >
            <RefreshCw size={12} />
            重新加载
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
