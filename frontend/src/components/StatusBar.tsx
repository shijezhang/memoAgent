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
