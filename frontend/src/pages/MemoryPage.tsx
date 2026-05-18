import { useEffect, useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { Brain, Database, MessageSquare, RefreshCw, Trash2, BookOpen } from 'lucide-react'
import { useStore } from '../store/useStore'
import { memoryApi, reflectionApi } from '../api/client'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import type { KGNode } from '../api/types'

function MemoryPage() {
  const memoryStatus = useStore((state) => state.memoryStatus)
  const fetchMemoryStatus = useStore((state) => state.fetchMemoryStatus)
  const [guidelines, setGuidelines] = useState<KGNode[]>([])
  const [searchTerm, setSearchTerm] = useState('')

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

  const filteredGuidelines = useMemo(() =>
    guidelines.filter((g) =>
      g.rule?.toLowerCase().includes(searchTerm.toLowerCase())
    ),
    [guidelines, searchTerm]
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
            aria-label="刷新"
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
                    aria-label="清空情节记忆"
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
                aria-label="搜索 Guidelines"
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
