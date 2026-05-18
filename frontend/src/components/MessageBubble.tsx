import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { CodeBlock } from './CodeBlock'
import { cn } from '../lib/cn'
import type { Message } from '../store/useStore'

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn('flex mb-4', isUser ? 'justify-end' : 'justify-start')}
    >
      <div
        className={cn(
          'max-w-[70%] px-4 py-2.5',
          isUser
            ? 'bg-primary-500 text-white rounded-2xl rounded-bl-md'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-2xl rounded-br-md'
        )}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <ReactMarkdown
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  const isInline = !match

                  if (isInline) {
                    return (
                      <code className="px-1 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-sm" {...props}>
                        {children}
                      </code>
                    )
                  }

                  return (
                    <CodeBlock code={String(children).replace(/\n$/, '')} language={match[1]} />
                  )
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-primary-500 animate-pulse ml-1" />
        )}

        {message.guidelines && message.guidelines.length > 0 && (
          <div className="mt-2 text-xs opacity-75 border-t border-gray-200 dark:border-gray-700 pt-2">
            <span className="font-medium">Guidelines: </span>
            {message.guidelines.join(', ')}
          </div>
        )}

        {message.isReflection && (
          <div className="mt-2 text-xs text-orange-500 font-medium">
            ✓ Reflection applied
          </div>
        )}
      </div>
    </motion.div>
  )
}
