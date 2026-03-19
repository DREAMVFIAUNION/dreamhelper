'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { Mic, MicOff, Volume2, Loader2, Phone, PhoneOff } from 'lucide-react'

interface TalkModeProps {
  onSendMessage: (text: string) => Promise<string>
  voice?: string
  className?: string
}

type TalkState = 'idle' | 'listening' | 'transcribing' | 'thinking' | 'speaking'

const STATE_LABELS: Record<TalkState, string> = {
  idle: '点击开始对话',
  listening: '正在聆听...',
  transcribing: '识别中...',
  thinking: '思考中...',
  speaking: '回答中...',
}

const STATE_COLORS: Record<TalkState, string> = {
  idle: 'border-gray-600',
  listening: 'border-red-500 shadow-red-500/30',
  transcribing: 'border-yellow-500 shadow-yellow-500/30',
  thinking: 'border-cyan-500 shadow-cyan-500/30',
  speaking: 'border-green-500 shadow-green-500/30',
}

export default function TalkMode({ onSendMessage, voice = 'xiaoxiao', className = '' }: TalkModeProps) {
  const [active, setActive] = useState(false)
  const [state, setState] = useState<TalkState>('idle')
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [volume, setVolume] = useState(0)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number>(0)
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // VAD 参数
  const VAD_THRESHOLD = 0.02      // 音量阈值
  const SILENCE_TIMEOUT = 1500    // 静音超时 ms

  const cleanup = useCallback(() => {
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current)
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    streamRef.current?.getTracks().forEach(t => t.stop())
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    analyserRef.current = null
    mediaRecorderRef.current = null
    streamRef.current = null
  }, [])

  const stopTalkMode = useCallback(() => {
    cleanup()
    setActive(false)
    setState('idle')
    setVolume(0)
  }, [cleanup])

  const speak = useCallback(async (text: string): Promise<void> => {
    setState('speaking')
    setResponse(text)
    try {
      const res = await fetch('/api/multimodal/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice }),
      })
      if (!res.ok) return

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current = audio

      return new Promise<void>((resolve) => {
        audio.onended = () => {
          URL.revokeObjectURL(url)
          resolve()
        }
        audio.onerror = () => {
          URL.revokeObjectURL(url)
          resolve()
        }
        audio.play().catch(resolve)
      })
    } catch {
      // TTS failed, continue anyway
    }
  }, [voice])

  const transcribe = useCallback(async (blob: Blob): Promise<string> => {
    setState('transcribing')
    try {
      const formData = new FormData()
      formData.append('audio', blob, 'recording.webm')
      formData.append('language', 'zh')
      const res = await fetch('/api/multimodal/stt', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      return data.text || ''
    } catch {
      return ''
    }
  }, [])

  const processRecording = useCallback(async (blob: Blob) => {
    // STT
    const text = await transcribe(blob)
    if (!text.trim()) {
      setState('listening')
      return
    }
    setTranscript(text)

    // LLM
    setState('thinking')
    const reply = await onSendMessage(text)

    // TTS
    await speak(reply)

    // 回到聆听状态
    setState('listening')
    startListening()
  }, [transcribe, onSendMessage, speak])

  const startListening = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      // 音量分析
      const audioCtx = new AudioContext()
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 512
      source.connect(analyser)
      analyserRef.current = analyser

      const dataArray = new Uint8Array(analyser.frequencyBinCount)
      let isVoiceActive = false

      const checkVolume = () => {
        if (!analyserRef.current) return
        analyserRef.current.getByteTimeDomainData(dataArray)
        let sum = 0
        for (let i = 0; i < dataArray.length; i++) {
          const v = (dataArray[i]! - 128) / 128
          sum += v * v
        }
        const rms = Math.sqrt(sum / dataArray.length)
        setVolume(rms)

        if (rms > VAD_THRESHOLD) {
          if (!isVoiceActive) {
            // 开始录音
            isVoiceActive = true
            startRecordingChunks(stream)
          }
          // 重置静音计时器
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current)
          silenceTimerRef.current = setTimeout(() => {
            // 静音超时 → 停止录音
            if (isVoiceActive && mediaRecorderRef.current?.state === 'recording') {
              isVoiceActive = false
              mediaRecorderRef.current.stop()
            }
          }, SILENCE_TIMEOUT)
        }

        animFrameRef.current = requestAnimationFrame(checkVolume)
      }
      animFrameRef.current = requestAnimationFrame(checkVolume)

      setState('listening')
    } catch {
      stopTalkMode()
    }
  }, [stopTalkMode])

  const startRecordingChunks = useCallback((stream: MediaStream) => {
    const recorder = new MediaRecorder(stream, {
      mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm',
    })
    mediaRecorderRef.current = recorder
    chunksRef.current = []

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data)
    }

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
      if (blob.size > 1000) {
        // 有效录音 → 处理
        processRecording(blob)
      }
    }

    recorder.start()
  }, [processRecording])

  const startTalkMode = useCallback(async () => {
    setActive(true)
    setTranscript('')
    setResponse('')
    await startListening()
  }, [startListening])

  // 清理
  useEffect(() => {
    return () => { cleanup() }
  }, [cleanup])

  if (!active) {
    return (
      <button
        onClick={startTalkMode}
        className={`flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-cyan-600/20 to-purple-600/20 border border-cyan-500/30 text-cyan-400 hover:border-cyan-400/60 hover:text-cyan-300 transition-all ${className}`}
      >
        <Phone size={16} />
        <span className="text-sm">Talk Mode</span>
      </button>
    )
  }

  return (
    <div className={`flex flex-col items-center gap-4 p-6 rounded-2xl bg-[#0a0e1a]/80 border ${STATE_COLORS[state]} shadow-lg transition-all ${className}`}>
      {/* 音量可视化环 */}
      <div className="relative">
        <div
          className={`w-24 h-24 rounded-full border-4 flex items-center justify-center transition-all ${STATE_COLORS[state]}`}
          style={{
            transform: `scale(${1 + volume * 3})`,
            boxShadow: state === 'listening' ? `0 0 ${20 + volume * 100}px rgba(239,68,68,0.3)` : undefined,
          }}
        >
          {state === 'listening' && <Mic size={32} className="text-red-400 animate-pulse" />}
          {state === 'transcribing' && <Loader2 size={32} className="text-yellow-400 animate-spin" />}
          {state === 'thinking' && <Loader2 size={32} className="text-cyan-400 animate-spin" />}
          {state === 'speaking' && <Volume2 size={32} className="text-green-400 animate-pulse" />}
          {state === 'idle' && <MicOff size={32} className="text-gray-500" />}
        </div>
      </div>

      {/* 状态文字 */}
      <div className="text-center">
        <div className="text-sm text-gray-400">{STATE_LABELS[state]}</div>
        {transcript && (
          <div className="mt-2 text-xs text-cyan-300/70 max-w-xs truncate">
            你: {transcript}
          </div>
        )}
        {response && state === 'speaking' && (
          <div className="mt-1 text-xs text-green-300/70 max-w-xs truncate">
            助手: {response.slice(0, 80)}...
          </div>
        )}
      </div>

      {/* 停止按钮 */}
      <button
        onClick={stopTalkMode}
        className="flex items-center gap-2 px-4 py-2 rounded-full bg-red-600/20 border border-red-500/40 text-red-400 hover:bg-red-600/30 transition-all"
      >
        <PhoneOff size={14} />
        <span className="text-xs">结束通话</span>
      </button>
    </div>
  )
}
