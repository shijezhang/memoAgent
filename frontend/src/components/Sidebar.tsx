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
              <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 bg-primary-500 rounded-r" />
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
