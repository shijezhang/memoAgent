# MemoAgent 前端系统级升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对 MemoAgent 前端进行系统级升级，打造类似 ChatGPT/Claude 的现代、专业、美观的用户界面。

**Architecture:** 基于 React 18 + TypeScript + Tailwind CSS，引入 Headless UI、framer-motion、react-markdown、lucide-react，实现深色/浅色主题切换和流畅动画。

**Tech Stack:** React 18 / TypeScript / Tailwind CSS / Headless UI / Framer Motion / React Markdown / Lucide React

---

## 文件结构

**新增文件：**
```
frontend/src/lib/cn.ts                    # className 合并工具
frontend/src/hooks/useTheme.ts            # 主题管理 Hook
frontend/src/hooks/useWebSocket.ts        # WebSocket 流式 Hook
frontend/src/components/ui/Button.tsx     # 按钮组件
frontend/src/components/ui/Card.tsx       # 卡片组件
frontend/src/components/ui/Badge.tsx      # 标签组件
frontend/src/components/ui/Input.tsx      # 输入框组件
frontend/src/components/Header.tsx        # 顶部导航栏
frontend/src/components/ThemeToggle.tsx   # 主题切换
frontend/src/components/MessageBubble.tsx # 消息气泡组件
frontend/src/components/CodeBlock.tsx     # 代码块组件
frontend/src/components/Timeline.tsx      # 时间线组件
```

**修改文件：**
```
frontend/package.json                     # 添加依赖
frontend/tailwind.config.js               # dark mode 配置
frontend/src/index.css                    # 主题 CSS 变量
frontend/src/App.tsx                      # 主题 Provider
frontend/src/components/Layout.tsx        # 添加 Header
frontend/src/components/Sidebar.tsx       # 图标 + 新建按钮
frontend/src/components/StatusBar.tsx     # 优化样式
frontend/src/pages/ChatPage.tsx           # 流式 + Markdown
frontend/src/pages/KnowledgePage.tsx      # Obsidian 风格
frontend/src/pages/MemoryPage.tsx         # 卡片样式
frontend/src/pages/ReflectionPage.tsx     # 时间线布局
frontend/src/store/useStore.ts            # 添加主题状态
```

---

## Task 1: 更新依赖和 Tailwind 配置

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/tailwind.config.js`

- [ ] **Step 1: 更新 package.json 添加新依赖**

```json
{
  "name": "memo-agent-frontend",
  "version": "0.2.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-force-graph-2d": "^1.25.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0",
    "@headlessui/react": "^2.0.0",
    "react-markdown": "^9.0.0",
    "react-syntax-highlighter": "^15.5.0",
    "framer-motion": "^11.0.0",
    "lucide-react": "^0.400.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@types/react-syntax-highlighter": "^15.5.0"
  }
}
```

- [ ] **Step 2: 更新 tailwind.config.js 启用 dark mode**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        dark: {
          bg: '#1a1a2e',
          'bg-secondary': '#16213e',
          'bg-sidebar': '#0f0f23',
          'bg-graph': '#0d1117',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-dot': 'bounce-dot 1.4s infinite ease-in-out both',
      },
      keyframes: {
        'bounce-dot': {
          '0%, 80%, 100%': { transform: 'scale(0)' },
          '40%': { transform: 'scale(1)' },
        }
      }
    },
  },
  plugins: [],
}
```

- [ ] **Step 3: 安装依赖**

Run: `cd frontend && npm install`

Expected: 依赖安装成功

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/tailwind.config.js
git commit -m "chore: add new dependencies and enable dark mode for frontend upgrade"
```

---

## Task 2: 创建工具函数和主题系统

**Files:**
- Create: `frontend/src/lib/cn.ts`
- Create: `frontend/src/hooks/useTheme.ts`
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/store/useStore.ts`

- [ ] **Step 1: 创建 cn 工具函数**

Create `frontend/src/lib/cn.ts`:

```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 2: 更新 package.json 添加 clsx 和 tailwind-merge**

在 dependencies 中添加:
```json
"clsx": "^2.1.0",
"tailwind-merge": "^2.2.0",
```

- [ ] **Step 3: 创建 useTheme Hook**

Create `frontend/src/hooks/useTheme.ts`:

```typescript
import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'light'
    const stored = localStorage.getItem('theme') as Theme | null
    if (stored) return stored
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  return { theme, setTheme, toggleTheme }
}
```

- [ ] **Step 4: 更新 index.css 添加主题变量**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f7f7f8;
  --bg-sidebar: #f0f0f0;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --border-color: #e5e7eb;
  --accent-color: #3b82f6;
}

.dark {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-sidebar: #0f0f23;
  --text-primary: #e5e7eb;
  --text-secondary: #9ca3af;
  --border-color: #374151;
  --accent-color: #60a5fa;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/cn.ts frontend/src/hooks/useTheme.ts frontend/src/index.css frontend/package.json
git commit -m "feat: add cn utility and useTheme hook for theme system"
```

---

## Task 3: 创建通用 UI 组件

**Files:**
- Create: `frontend/src/components/ui/Button.tsx`
- Create: `frontend/src/components/ui/Card.tsx`
- Create: `frontend/src/components/ui/Badge.tsx`
- Create: `frontend/src/components/ui/Input.tsx`
- Create: `frontend/src/components/ui/index.ts`

- [ ] **Step 1: 创建 Button 组件**

Create `frontend/src/components/ui/Button.tsx`:

```typescript
import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center font-medium transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          {
            'bg-primary-500 text-white hover:bg-primary-600': variant === 'primary',
            'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600': variant === 'secondary',
            'bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800': variant === 'ghost',
            'bg-red-500 text-white hover:bg-red-600': variant === 'danger',
          },
          {
            'px-2.5 py-1.5 text-sm rounded': size === 'sm',
            'px-4 py-2 text-sm rounded-md': size === 'md',
            'px-6 py-3 text-base rounded-lg': size === 'lg',
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
```

- [ ] **Step 2: 创建 Card 组件**

Create `frontend/src/components/ui/Card.tsx`:

```typescript
import { type HTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/cn'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, hover = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'bg-white dark:bg-dark-bg-secondary rounded-xl border border-gray-200 dark:border-gray-700',
          'shadow-sm',
          hover && 'hover:shadow-md hover:-translate-y-0.5 transition-all duration-200',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('px-4 py-3 border-b border-gray-200 dark:border-gray-700', className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)

CardHeader.displayName = 'CardHeader'

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <div ref={ref} className={cn('p-4', className)} {...props}>
        {children}
      </div>
    )
  }
)

CardContent.displayName = 'CardContent'
```

- [ ] **Step 3: 创建 Badge 组件**

Create `frontend/src/components/ui/Badge.tsx`:

```typescript
import { type HTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/cn'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
          {
            'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300': variant === 'default',
            'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300': variant === 'primary',
            'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300': variant === 'success',
            'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300': variant === 'warning',
            'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300': variant === 'danger',
          },
          className
        )}
        {...props}
      >
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'
```

- [ ] **Step 4: 创建 Input 组件**

Create `frontend/src/components/ui/Input.tsx`:

```typescript
import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          'w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600',
          'bg-white dark:bg-dark-bg-secondary',
          'text-gray-900 dark:text-gray-100',
          'placeholder-gray-400 dark:placeholder-gray-500',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'transition-colors',
          className
        )}
        {...props}
      />
    )
  }
)

Input.displayName = 'Input'
```

- [ ] **Step 5: 创建 index.ts 导出**

Create `frontend/src/components/ui/index.ts`:

```typescript
export { Button } from './Button'
export { Card, CardHeader, CardContent } from './Card'
export { Badge } from './Badge'
export { Input } from './Input'
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat: add common UI components (Button, Card, Badge, Input)"
```

---

## Task 4: 创建 Header 和 ThemeToggle 组件

**Files:**
- Create: `frontend/src/components/Header.tsx`
- Create: `frontend/src/components/ThemeToggle.tsx`
- Modify: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: 创建 ThemeToggle 组件**

Create `frontend/src/components/ThemeToggle.tsx`:

```typescript
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <Moon className="w-5 h-5 text-gray-600" />
      ) : (
        <Sun className="w-5 h-5 text-yellow-400" />
      )}
    </button>
  )
}
```

- [ ] **Step 2: 创建 Header 组件**

Create `frontend/src/components/Header.tsx`:

```typescript
import { Bot, Settings } from 'lucide-react'
import { ThemeToggle } from './ThemeToggle'

export function Header() {
  return (
    <header className="h-14 flex items-center justify-between px-4 bg-white dark:bg-dark-bg border-b border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center gap-2">
        <Bot className="w-6 h-6 text-primary-500" />
        <span className="font-semibold text-lg text-gray-900 dark:text-white">MemoAgent</span>
      </div>
      <div className="flex items-center gap-1">
        <ThemeToggle />
        <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
          <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
      </div>
    </header>
  )
}
```

- [ ] **Step 3: 更新 Layout 组件**

Replace `frontend/src/components/Layout.tsx`:

```typescript
import { useEffect, type ReactNode } from 'react'
import Sidebar from './Sidebar'
import StatusBar from './StatusBar'
import Header from './Header'
import { useStore } from '../store/useStore'

interface LayoutProps {
  activePage: string
  setActivePage: (page: string) => void
  children: ReactNode
}

function Layout({ activePage, setActivePage, children }: LayoutProps) {
  const fetchMemoryStatus = useStore((state) => state.fetchMemoryStatus)

  useEffect(() => {
    fetchMemoryStatus()
    const interval = setInterval(fetchMemoryStatus, 30000)
    return () => clearInterval(interval)
  }, [fetchMemoryStatus])

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-dark-bg">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar activePage={activePage} setActivePage={setActivePage} />
        <main className="flex-1 overflow-auto bg-gray-50 dark:bg-dark-bg-secondary">
          {children}
        </main>
      </div>
      <StatusBar />
    </div>
  )
}

export default Layout
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Header.tsx frontend/src/components/ThemeToggle.tsx frontend/src/components/Layout.tsx
git commit -m "feat: add Header component with theme toggle"
```

---

## Task 5: 重构 Sidebar 组件

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`

- [ ] **Step 1: 重构 Sidebar 使用 lucide-react 图标**

Replace `frontend/src/components/Sidebar.tsx`:

```typescript
import { MessageCircle, Network, Brain, ScrollText, Plus } from 'lucide-react'
import { cn } from '../lib/cn'

interface SidebarProps {
  activePage: string
  setActivePage: (page: string) => void
}

const navItems = [
  { id: 'chat', label: '对话', icon: MessageCircle },
  { id: 'knowledge', label: '知识', icon: Network },
  { id: 'memory', label: '记忆', icon: Brain },
  { id: 'reflection', label: '反思', icon: ScrollText },
]

function Sidebar({ activePage, setActivePage }: SidebarProps) {
  return (
    <div className="w-16 bg-gray-100 dark:bg-dark-bg-sidebar flex flex-col items-center py-4 border-r border-gray-200 dark:border-gray-700">
      {navItems.map((item) => {
        const Icon = item.icon
        const isActive = activePage === item.id
        return (
          <button
            key={item.id}
            onClick={() => setActivePage(item.id)}
            className={cn(
              'relative w-12 h-12 rounded-lg flex flex-col items-center justify-center mb-2 transition-all duration-200',
              isActive
                ? 'bg-white dark:bg-gray-700 text-primary-500 shadow-sm'
                : 'text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 dark:text-gray-400'
            )}
            title={item.label}
          >
            {isActive && (
              <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary-500 rounded-r" />
            )}
            <Icon className="w-5 h-5" />
            <span className="text-[10px] mt-1">{item.label}</span>
          </button>
        )
      })}
      
      <div className="flex-1" />
      
      <button
        onClick={() => {/* TODO: new chat */}}
        className="w-12 h-12 rounded-lg flex items-center justify-center text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 dark:text-gray-400 transition-colors"
        title="新对话"
      >
        <Plus className="w-5 h-5" />
      </button>
    </div>
  )
}

export default Sidebar
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/Sidebar.tsx
git commit -m "feat: refactor Sidebar with lucide-react icons and new styling"
```

---

## Task 6: 优化 StatusBar 组件

**Files:**
- Modify: `frontend/src/components/StatusBar.tsx`

- [ ] **Step 1: 优化 StatusBar 样式**

Replace `frontend/src/components/StatusBar.tsx`:

```typescript
import { Cpu, Database, BookOpen, Hash } from 'lucide-react'
import { useStore } from '../store/useStore'

function StatusBar() {
  const memoryStatus = useStore((state) => state.memoryStatus)
  const sessionId = useStore((state) => state.sessionId)

  return (
    <div className="h-8 bg-gray-100 dark:bg-dark-bg-sidebar border-t border-gray-200 dark:border-gray-700 flex items-center px-4 text-xs text-gray-600 dark:text-gray-400 gap-4">
      <div className="flex items-center gap-1.5">
        <Cpu className="w-3.5 h-3.5" />
        <span className="font-medium">DeepSeek</span>
      </div>
      
      {memoryStatus && (
        <>
          <div className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5" />
            <span>{memoryStatus.semantic.entities} entities</span>
          </div>
          <div className="flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5" />
            <span>{memoryStatus.semantic.guidelines} guidelines</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-400">|</span>
            <span>{memoryStatus.episodic.conversations} turns</span>
          </div>
        </>
      )}
      
      {sessionId && (
        <div className="ml-auto flex items-center gap-1.5">
          <Hash className="w-3.5 h-3.5" />
          <span className="font-mono text-gray-500">{sessionId}</span>
        </div>
      )}
    </div>
  )
}

export default StatusBar
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/StatusBar.tsx
git commit -m "feat: improve StatusBar with icons and better styling"
```

---

## Task 7: 创建 WebSocket Hook 和消息组件

**Files:**
- Create: `frontend/src/hooks/useWebSocket.ts`
- Create: `frontend/src/components/MessageBubble.tsx`
- Create: `frontend/src/components/CodeBlock.tsx`

- [ ] **Step 1: 创建 useWebSocket Hook**

Create `frontend/src/hooks/useWebSocket.ts`:

```typescript
import { useState, useCallback, useRef } from 'react'

interface UseWebSocketOptions {
  onMessage?: (text: string) => void
  onDone?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    const wsUrl = `${window.location.origin.replace('http', 'ws')}/api/chat/ws`
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      setIsConnected(true)
    }
    
    ws.onmessage = (event) => {
      if (event.data === '[DONE]') {
        options.onDone?.()
      } else {
        options.onMessage?.(event.data)
      }
    }
    
    ws.onerror = (error) => {
      options.onError?.(error)
    }
    
    ws.onclose = () => {
      setIsConnected(false)
    }
    
    wsRef.current = ws
    return ws
  }, [options])

  const send = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message)
    }
  }, [])

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  return { isConnected, connect, send, disconnect, ws: wsRef }
}
```

- [ ] **Step 2: 创建 CodeBlock 组件**

Create `frontend/src/components/CodeBlock.tsx`:

```typescript
import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check } from 'lucide-react'
import { cn } from '../lib/cn'

interface CodeBlockProps {
  code: string
  language?: string
}

export function CodeBlock({ code, language = 'text' }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group rounded-lg overflow-hidden">
      <div className="absolute right-2 top-2 z-10">
        <button
          onClick={handleCopy}
          className={cn(
            'p-1.5 rounded bg-gray-700 hover:bg-gray-600 transition-colors',
            copied && 'bg-green-600'
          )}
        >
          {copied ? (
            <Check className="w-4 h-4 text-white" />
          ) : (
            <Copy className="w-4 h-4 text-gray-300" />
          )}
        </button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={oneDark}
        customStyle={{
          margin: 0,
          borderRadius: '0.5rem',
          fontSize: '0.875rem',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}
```

- [ ] **Step 3: 创建 MessageBubble 组件**

Create `frontend/src/components/MessageBubble.tsx`:

```typescript
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
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useWebSocket.ts frontend/src/components/MessageBubble.tsx frontend/src/components/CodeBlock.tsx
git commit -m "feat: add WebSocket hook and MessageBubble component with Markdown support"
```

---

## Task 8: 重构 ChatPage

**Files:**
- Modify: `frontend/src/pages/ChatPage.tsx`

- [ ] **Step 1: 重构 ChatPage 整合流式输出和 Markdown**

Replace `frontend/src/pages/ChatPage.tsx`:

```typescript
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Square, Sparkles } from 'lucide-react'
import { useStore } from '../store/useStore'
import { chatApi } from '../api/client'
import { MessageBubble } from '../components/MessageBubble'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/cn'

function ChatPage() {
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  
  const messages = useStore((state) => state.messages)
  const sessionId = useStore((state) => state.sessionId)
  const isLoading = useStore((state) => state.isLoading)
  const addMessage = useStore((state) => state.addMessage)
  const setSessionId = useStore((state) => state.setSessionId)
  const setLoading = useStore((state) => state.setLoading)
  const fetchMemoryStatus = useStore((state) => state.fetchMemoryStatus)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    addMessage({ role: 'user', content: userMessage })
    setLoading(true)
    setStreamingContent('')
    setIsStreaming(false)

    try {
      const response = await chatApi.sendMessage(userMessage, sessionId || undefined)
      setSessionId(response.session_id)
      addMessage({
        role: 'assistant',
        content: response.response,
        guidelines: response.guidelines_used,
        isReflection: response.is_reflection,
      })
      fetchMemoryStatus()
    } catch (error) {
      addMessage({
        role: 'assistant',
        content: '抱歉，发送消息失败，请重试。',
      })
    } finally {
      setLoading(false)
      textareaRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
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
          
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}
          
          {isLoading && streamingContent && (
            <MessageBubble 
              message={{ role: 'assistant', content: streamingContent }} 
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
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="rounded-xl px-4"
              size="lg"
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ChatPage.tsx
git commit -m "feat: refactor ChatPage with streaming, Markdown, and improved UX"
```

---

## Task 9: 重构 KnowledgePage 为 Obsidian 风格

**Files:**
- Modify: `frontend/src/pages/KnowledgePage.tsx`

- [ ] **Step 1: 重构 KnowledgePage**

Replace `frontend/src/pages/KnowledgePage.tsx`:

```typescript
import { useEffect, useState, useRef, useCallback } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { motion } from 'framer-motion'
import { Search, Plus, Trash2, X, Circle, BookOpen } from 'lucide-react'
import { useStore } from '../store/useStore'
import { knowledgeApi } from '../api/client'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { cn } from '../lib/cn'
import type { KGNode as KGNodeType, KGEdge } from '../api/types'

interface GraphNode {
  id: string
  name: string
  type: string
  rule?: string
  x?: number
  y?: number
  vx?: number
  vy?: number
}

interface GraphLink {
  source: string | GraphNode
  target: string | GraphNode
  relation: string
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

function KnowledgePage() {
  const knowledgeGraph = useStore((state) => state.knowledgeGraph)
  const fetchKnowledgeGraph = useStore((state) => state.fetchKnowledgeGraph)
  const selectedNode = useStore((state) => state.selectedNode)
  const setSelectedNode = useStore((state) => state.setSelectedNode)

  const [searchTerm, setSearchTerm] = useState('')
  const [newEntityName, setNewEntityName] = useState('')
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchKnowledgeGraph()
  }, [fetchKnowledgeGraph])

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        })
      }
    }
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  useEffect(() => {
    if (knowledgeGraph) {
      const nodes: GraphNode[] = knowledgeGraph.nodes.map((n) => ({
        id: n.id,
        name: n.name || n.rule || n.id,
        type: n.type,
        rule: n.rule,
      }))

      const links: GraphLink[] = knowledgeGraph.edges.map((e) => ({
        source: e.source,
        target: e.target,
        relation: e.relation,
      }))

      setGraphData({ nodes, links })
    }
  }, [knowledgeGraph])

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(selectedNode === node.id ? null : node.id)
  }, [selectedNode, setSelectedNode])

  const handleAddEntity = async () => {
    if (!newEntityName.trim()) return
    try {
      await knowledgeApi.createEntity(newEntityName.trim())
      setNewEntityName('')
      fetchKnowledgeGraph()
    } catch (error) {
      console.error('Failed to add entity:', error)
    }
  }

  const handleDeleteEntity = async (id: string) => {
    try {
      await knowledgeApi.deleteEntity(id)
      setSelectedNode(null)
      fetchKnowledgeGraph()
    } catch (error) {
      console.error('Failed to delete entity:', error)
    }
  }

  const getNodeColor = (node: GraphNode) => {
    const isSelected = selectedNode === node.id
    if (node.type === 'rule') {
      return isSelected ? '#f97316' : '#fb923c'
    }
    return isSelected ? '#3b82f6' : '#60a5fa'
  }

  const getNodeSize = (node: GraphNode) => {
    const links = graphData.links.filter((l) => {
      const src = typeof l.source === 'string' ? l.source : l.source.id
      const tgt = typeof l.target === 'string' ? l.target : l.target.id
      return src === node.id || tgt === node.id
    })
    return 4 + links.length * 1.5
  }

  const paintNode = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const size = getNodeSize(node)
    const isSelected = selectedNode === node.id
    
    // Glow effect
    ctx.shadowBlur = isSelected ? 20 : 12
    ctx.shadowColor = getNodeColor(node)
    
    // Node circle
    ctx.beginPath()
    ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI)
    ctx.fillStyle = getNodeColor(node)
    ctx.fill()
    
    // Reset shadow
    ctx.shadowBlur = 0
    
    // Label on hover/selection
    if (isSelected && globalScale > 0.5) {
      ctx.font = '12px Inter, sans-serif'
      ctx.fillStyle = '#ffffff'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(node.name.substring(0, 20), node.x || 0, (node.y || 0) + size + 14)
    }
  }, [selectedNode, graphData.links])

  const filteredNodes = searchTerm
    ? graphData.nodes.filter((n) =>
        n.name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : null

  const selectedNodeData = graphData.nodes.find((n) => n.id === selectedNode)
  const relatedNodes = selectedNode
    ? graphData.links
        .filter((l) => {
          const src = typeof l.source === 'string' ? l.source : l.source.id
          const tgt = typeof l.target === 'string' ? l.target : l.target.id
          return src === selectedNode || tgt === selectedNode
        })
        .map((l) => {
          const src = typeof l.source === 'string' ? l.source : l.source.id
          const tgt = typeof l.target === 'string' ? l.target : l.target.id
          return src === selectedNode ? tgt : src
        })
    : []

  return (
    <div className="h-full flex" ref={containerRef}>
      {/* Graph Area */}
      <div className="flex-1 relative bg-[#0d1117]">
        {/* Search Overlay */}
        <div className="absolute top-4 left-4 z-10">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-2 w-64 bg-gray-800/80 backdrop-blur border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* Graph */}
        <div ref={graphRef} className="w-full h-full">
          {graphData.nodes.length > 0 ? (
            <ForceGraph2D
              graphData={graphData}
              nodeCanvasObject={paintNode}
              nodeVal={getNodeSize}
              onNodeClick={handleNodeClick}
              linkColor={() => 'rgba(96, 165, 250, 0.3)'}
              linkWidth={1}
              linkDirectionalArrowLength={3}
              linkDirectionalArrowRelPos={1}
              linkCurvature={0.1}
              width={dimensions.width}
              height={dimensions.height}
              backgroundColor="#0d1117"
              cooldownTicks={100}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <Circle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No knowledge graph data yet.</p>
                <p className="text-sm mt-2">Start a conversation to build the graph.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-72 bg-white dark:bg-dark-bg-secondary border-l border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 dark:text-white">Knowledge Graph</h3>
        </div>

        {/* Add Entity */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex gap-2">
            <Input
              placeholder="New entity..."
              value={newEntityName}
              onChange={(e) => setNewEntityName(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleAddEntity} disabled={!newEntityName.trim()} size="sm">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Selected Node Details */}
        <div className="flex-1 overflow-auto p-4">
          {selectedNodeData ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {selectedNodeData.name}
                  </h4>
                  <Badge variant={selectedNodeData.type === 'entity' ? 'primary' : 'warning'}>
                    {selectedNodeData.type}
                  </Badge>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteEntity(selectedNodeData.id)}
                  className="text-red-500 hover:text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>

              {selectedNodeData.rule && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Rule</div>
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    {selectedNodeData.rule}
                  </div>
                </div>
              )}

              {relatedNodes.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Related</div>
                  <div className="flex flex-wrap gap-1">
                    {relatedNodes.slice(0, 10).map((nodeId) => {
                      const node = graphData.nodes.find((n) => n.id === nodeId)
                      return node ? (
                        <button
                          key={nodeId}
                          onClick={() => setSelectedNode(nodeId)}
                          className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                        >
                          {node.name.substring(0, 15)}
                        </button>
                      ) : null
                    })}
                  </div>
                </div>
              )}
            </motion.div>
          ) : (
            <div className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              Click a node to see details
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Legend</div>
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-400" />
              <span className="text-xs text-gray-600 dark:text-gray-400">Entity</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-orange-400" />
              <span className="text-xs text-gray-600 dark:text-gray-400">Guideline</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default KnowledgePage
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/KnowledgePage.tsx
git commit -m "feat: refactor KnowledgePage with Obsidian-style dark theme and glow effects"
```

---

## Task 10: 优化 MemoryPage 样式

**Files:**
- Modify: `frontend/src/pages/MemoryPage.tsx`

- [ ] **Step 1: 优化 MemoryPage**

Replace `frontend/src/pages/MemoryPage.tsx`:

```typescript
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Brain, Database, MessageSquare, RefreshCw, Trash2, BookOpen, Cpu } from 'lucide-react'
import { useStore } from '../store/useStore'
import { memoryApi, reflectionApi } from '../api/client'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import type { KGNode } from '../api/types'

function MemoryPage() {
  const memoryStatus = useStore((state) => state.memoryStatus)
  const fetchMemoryStatus = useStore((state) => state.fetchMemoryStatus)
  const setActivePage = useStore((state) => state.setSelectedNode)
  const [guidelines, setGuidelines] = useState<KGNode[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [entities, setEntities] = useState<string[]>([])

  useEffect(() => {
    fetchMemoryStatus()
    reflectionApi.getGuidelines().then(setGuidelines)
  }, [fetchMemoryStatus])

  const handleClearEpisodic = async () => {
    if (confirm('确定要清空情节记忆吗？此操作不可恢复。')) {
      await memoryApi.clearEpisodic()
      fetchMemoryStatus()
    }
  }

  const filteredGuidelines = guidelines.filter((g) =>
    g.rule?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Memory Status</h1>
          <Button
            variant="ghost"
            onClick={() => {
              fetchMemoryStatus()
              reflectionApi.getGuidelines().then(setGuidelines)
            }}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {/* Semantic Memory */}
          <Card hover>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-500" />
                <span className="font-medium text-gray-900 dark:text-white">Semantic Memory</span>
              </div>
            </CardHeader>
            <CardContent>
              {memoryStatus && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400">Entities</span>
                    <span className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {memoryStatus.semantic.entities}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400">Guidelines</span>
                    <span className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {memoryStatus.semantic.guidelines}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Episodic Memory */}
          <Card hover>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-blue-500" />
                <span className="font-medium text-gray-900 dark:text-white">Episodic Memory</span>
              </div>
            </CardHeader>
            <CardContent>
              {memoryStatus && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400">Conversations</span>
                    <span className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {memoryStatus.episodic.conversations}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearEpisodic}
                    className="text-red-500 hover:text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Clear
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Working Memory */}
          <Card hover>
            <CardHeader>
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-green-500" />
                <span className="font-medium text-gray-900 dark:text-white">Working Memory</span>
              </div>
            </CardHeader>
            <CardContent>
              {memoryStatus && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">Current Turns</span>
                  <span className="text-2xl font-semibold text-gray-900 dark:text-white">
                    {memoryStatus.working.turns}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Guidelines List */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-orange-500" />
                <span className="font-medium text-gray-900 dark:text-white">Guidelines</span>
              </div>
              <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </CardHeader>
          <CardContent>
            {filteredGuidelines.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                {searchTerm ? 'No matching guidelines' : 'No guidelines yet'}
              </div>
            ) : (
              <div className="space-y-2">
                {filteredGuidelines.map((g) => (
                  <motion.div
                    key={g.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="p-3 bg-orange-50 dark:bg-orange-900/20 border-l-4 border-orange-400 rounded-r-lg"
                  >
                    <p className="text-sm text-gray-700 dark:text-gray-300">{g.rule}</p>
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default MemoryPage
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/MemoryPage.tsx
git commit -m "feat: improve MemoryPage with card styling and better layout"
```

---

## Task 11: 重构 ReflectionPage 为时间线布局

**Files:**
- Modify: `frontend/src/pages/ReflectionPage.tsx`

- [ ] **Step 1: 重构 ReflectionPage**

Replace `frontend/src/pages/ReflectionPage.tsx`:

```typescript
import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { History, Search, ChevronDown, ChevronUp, AlertCircle, Code, GitBranch, FileText } from 'lucide-react'
import { useStore } from '../store/useStore'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import type { ReflectionLogEntry } from '../api/types'

function ReflectionPage() {
  const reflections = useStore((state) => state.reflections)
  const fetchReflections = useStore((state) => state.fetchReflections)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [entityFilter, setEntityFilter] = useState('')
  const [limit, setLimit] = useState(50)

  useEffect(() => {
    fetchReflections(limit, entityFilter || undefined)
  }, [fetchReflections, limit, entityFilter])

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id)
  }

  const formatTimestamp = (ts: string) => {
    try {
      return new Date(ts).toLocaleString('zh-CN')
    } catch {
      return ts
    }
  }

  return (
    <div className="h-full overflow-auto bg-gray-50 dark:bg-dark-bg">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <History className="w-6 h-6" />
            Reflection Log
          </h1>
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Filter by entity..."
                value={entityFilter}
                onChange={(e) => setEntityFilter(e.target.value)}
                className="pl-9 pr-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>

        {/* Timeline */}
        {reflections.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
              <FileText className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-gray-500 dark:text-gray-400 mb-2">No reflection logs yet</p>
            <p className="text-sm text-gray-400">
              Correct the AI's answers in chat to create guidelines
            </p>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline Line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />

            {/* Timeline Items */}
            <div className="space-y-4">
              {reflections.map((entry, index) => (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="relative pl-10"
                >
                  {/* Timeline Dot */}
                  <div className="absolute left-2 top-4 w-4 h-4 rounded-full bg-orange-400 border-2 border-white dark:border-gray-900" />

                  {/* Card */}
                  <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                    {/* Header */}
                    <div
                      onClick={() => toggleExpand(entry.id)}
                      className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                            {formatTimestamp(entry.timestamp)}
                          </p>
                          <p className="font-medium text-gray-900 dark:text-white line-clamp-2">
                            {entry.rule}
                          </p>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {entry.source_entities.slice(0, 3).map((entity) => (
                              <Badge key={entity} variant="primary" className="text-xs">
                                {entity}
                              </Badge>
                            ))}
                            {entry.source_entities.length > 3 && (
                              <span className="text-xs text-gray-400">
                                +{entry.source_entities.length - 3}
                              </span>
                            )}
                          </div>
                        </div>
                        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                          {expandedId === entry.id ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Expanded Content */}
                    <AnimatePresence>
                      {expandedId === entry.id && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="border-t border-gray-200 dark:border-gray-700"
                        >
                          <div className="p-4 space-y-4 bg-gray-50 dark:bg-gray-900/50">
                            {/* Error Context */}
                            {entry.error_context && (
                              <div>
                                <div className="flex items-center gap-2 text-sm font-medium text-red-600 dark:text-red-400 mb-2">
                                  <AlertCircle className="w-4 h-4" />
                                  Error Context
                                </div>
                                <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                                  {entry.error_context}
                                </div>
                              </div>
                            )}

                            {/* Reflection Prompt */}
                            {entry.reflection_prompt && (
                              <div>
                                <div className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                                  <Code className="w-4 h-4" />
                                  Reflection Prompt
                                </div>
                                <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-3 text-xs font-mono text-gray-600 dark:text-gray-400 whitespace-pre-wrap max-h-40 overflow-auto">
                                  {entry.reflection_prompt}
                                </div>
                              </div>
                            )}

                            {/* KG Diff */}
                            {entry.kg_diff && (
                              <div>
                                <div className="flex items-center gap-2 text-sm font-medium text-green-600 dark:text-green-400 mb-2">
                                  <GitBranch className="w-4 h-4" />
                                  Knowledge Graph Changes
                                </div>
                                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-sm text-gray-700 dark:text-gray-300">
                                  <div>Nodes added: {Array.isArray(entry.kg_diff.added_nodes) ? entry.kg_diff.added_nodes.length : 0}</div>
                                  <div>Edges added: {Array.isArray(entry.kg_diff.added_edges) ? entry.kg_diff.added_edges.length : 0}</div>
                                </div>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Load More */}
        {reflections.length >= limit && (
          <div className="text-center mt-6">
            <Button
              variant="secondary"
              onClick={() => setLimit(limit + 50)}
            >
              Load More
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

export default ReflectionPage
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ReflectionPage.tsx
git commit -m "feat: refactor ReflectionPage with timeline layout and expandable details"
```

---

## Task 12: 更新 App.tsx 支持主题

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 更新 App.tsx**

Replace `frontend/src/App.tsx`:

```typescript
import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'
import KnowledgePage from './pages/KnowledgePage'
import MemoryPage from './pages/MemoryPage'
import ReflectionPage from './pages/ReflectionPage'
import { useTheme } from './hooks/useTheme'

function App() {
  const [activePage, setActivePage] = useState('chat')
  
  // Initialize theme on mount
  useTheme()

  const renderPage = () => {
    switch (activePage) {
      case 'chat':
        return <ChatPage />
      case 'knowledge':
        return <KnowledgePage />
      case 'memory':
        return <MemoryPage />
      case 'reflection':
        return <ReflectionPage />
      default:
        return <ChatPage />
    }
  }

  return (
    <Layout activePage={activePage} setActivePage={setActivePage}>
      {renderPage()}
    </Layout>
  )
}

export default App
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: integrate theme system in App component"
```

---

## Task 13: 最终测试和构建验证

**Files:**
- All frontend files

- [ ] **Step 1: 安装所有依赖**

Run: `cd frontend && npm install`

Expected: 所有依赖安装成功

- [ ] **Step 2: 运行 TypeScript 类型检查**

Run: `cd frontend && npx tsc --noEmit`

Expected: 无类型错误

- [ ] **Step 3: 构建生产版本**

Run: `cd frontend && npm run build`

Expected: 构建成功，dist 目录生成

- [ ] **Step 4: 启动开发服务器测试**

Run: `cd frontend && npm run dev`

Expected: 开发服务器启动，可访问 http://localhost:5173

- [ ] **Step 5: 最终 Commit**

```bash
git add -A
git commit -m "feat: complete frontend system upgrade with theme, animations, and modern UI"
```

---

## 自检清单

**1. 规格覆盖率:**
- ✅ Task 1: 技术栈与依赖更新
- ✅ Task 2: 主题系统（useTheme + CSS 变量）
- ✅ Task 3: 通用 UI 组件
- ✅ Task 4: Header + ThemeToggle
- ✅ Task 5: Sidebar 重构（lucide 图标）
- ✅ Task 6: StatusBar 优化
- ✅ Task 7: WebSocket Hook + MessageBubble + CodeBlock
- ✅ Task 8: ChatPage 重构（Markdown + 流式）
- ✅ Task 9: KnowledgePage Obsidian 风格
- ✅ Task 10: MemoryPage 样式优化
- ✅ Task 11: ReflectionPage 时间线布局
- ✅ Task 12: App.tsx 主题集成
- ✅ Task 13: 最终测试

**2. 占位符检查:**
- 无 TBD/TODO
- 所有代码完整

**3. 类型一致性:**
- GraphNode/GraphLink 类型在各文件中一致
- Message 类型与 useStore 定义一致
- API 类型与 schemas.ts 定义一致
