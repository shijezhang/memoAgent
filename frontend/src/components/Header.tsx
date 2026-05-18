import { useState } from 'react'
import { Bot, Settings } from 'lucide-react'
import { ThemeToggle } from './ThemeToggle'
import SettingsModal from './SettingsModal'

function Header() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

  return (
    <>
      <header className="h-14 flex items-center justify-between px-4 bg-white dark:bg-dark-bg border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="flex items-center gap-2">
          <Bot className="w-6 h-6 text-primary-500" />
          <span className="font-semibold text-lg text-gray-900 dark:text-white">MemoAgent</span>
        </div>
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <button
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            onClick={() => setIsSettingsOpen(true)}
            aria-label="设置"
          >
            <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </header>
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
    </>
  )
}

export default Header
