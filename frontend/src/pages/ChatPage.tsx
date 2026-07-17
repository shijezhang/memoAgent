import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Square, Sparkles } from 'lucide-react'
import { useStore } from '../store/useStore'
import { chatApi } from '../api/client'
import { MessageBubble } from '../components/MessageBubble'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/cn'

function ChatPage() {
  const [input, setInput] = useState('')
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)

  const messages = useStore((state) => state.messages)
  const sessionId = useStore((state) => state.sessionId)
  const isLoading = useStore((state) => state.isLoading)
  const addMessage = useStore((state) => state.addMessage)
  const setSessionId = useStore((state) => state.setSessionId)
  const setLoading = useStore((state) => state.setLoading)
  const fetchMemoryStatus = useStore((state) => state.fetchMemoryStatus)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const stopStreamingRef = useRef(false)
  const streamingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStreamingRef.current = true
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current)
      }
    }
  }, [])

  // Typewriter effect
  const typewriterEffect = useCallback((text: string, index: number, callback: () => void) => {
    if (stopStreamingRef.current || index >= text.length) {
      callback()
      return
    }

    setStreamingContent(text.slice(0, index + 1))
    streamingTimeoutRef.current = setTimeout(() => {
      typewriterEffect(text, index + 1, callback)
    }, 20) // 20ms per character
  }, [])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    addMessage({ role: 'user', content: userMessage })
    setLoading(true)
    setStreamingContent('')
    setIsStreaming(true)
    stopStreamingRef.current = false

    try {
      const response = await chatApi.sendMessage(userMessage, sessionId || undefined)
      setSessionId(response.session_id)

      // Start typewriter effect
      typewriterEffect(response.response, 0, () => {
        // Called when streaming is complete
        if (!stopStreamingRef.current) {
          addMessage({
            role: 'assistant',
            content: response.response,
            guidelines: response.guidelines_used,
            isReflection: response.is_reflection,
          })
          fetchMemoryStatus()
        }
        setLoading(false)
        setIsStreaming(false)
        setStreamingContent('')
      })
    } catch (error) {
      addMessage({
        role: 'assistant',
        content: '抱歉，发送消息失败，请重试。',
      })
      setLoading(false)
      setIsStreaming(false)
    }
  }

  const handleStop = () => {
    stopStreamingRef.current = true
    if (streamingTimeoutRef.current) {
      clearTimeout(streamingTimeoutRef.current)
    }
    // Add whatever was streamed so far as a message
    if (streamingContent) {
      addMessage({
        role: 'assistant',
        content: streamingContent,
      })
    }
    setLoading(false)
    setIsStreaming(false)
    setStreamingContent('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (isStreaming) {
        handleStop()
      } else {
        handleSend()
      }
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Messages Area */}
      <div className="flex-1 overflow-auto p-4">
        <AnimatePresence mode="popLayout">
          {messages.length === 0 && !isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center h-full text-center"
            >
              <div className="w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-primary-500" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                MemoAgent 学术助手
              </h2>
              <p className="text-gray-500 dark:text-gray-400 max-w-md">
                输入学术问题开始对话。如果我的回答有误，请直接说"不对，..."来纠正，我会从中学习。
              </p>
            </motion.div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {isLoading && streamingContent && (
            <MessageBubble
              message={{ id: 'streaming', role: 'assistant', content: streamingContent }}
              isStreaming
            />
          )}

          {isLoading && !streamingContent && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-br-md px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce-dot" style={{ animationDelay: '0s' }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce-dot" style={{ animationDelay: '0.16s' }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce-dot" style={{ animationDelay: '0.32s' }} />
                </div>
              </div>
            </div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-dark-bg">
        <div className="max-w-3xl mx-auto">
          <div className="relative flex gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息... (Shift+Enter 换行)"
              rows={1}
              className={cn(
                'flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-600',
                'bg-white dark:bg-gray-800 px-4 py-3 pr-12',
                'text-gray-900 dark:text-gray-100 placeholder-gray-400',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'transition-all duration-200'
              )}
              disabled={isLoading}
            />
            <Button
              onClick={isStreaming ? handleStop : handleSend}
              disabled={isLoading && !isStreaming}
              className="rounded-xl px-4"
              size="lg"
              aria-label={isStreaming ? '停止生成' : '发送消息'}
            >
              {isLoading ? (
                <Square className="w-5 h-5" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </div>
          <div className="mt-2 text-xs text-gray-400 dark:text-gray-500 text-center">
            命令: <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">/help</kbd> |
            <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">/reflect</kbd> |
            <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">/memory status</kbd>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
