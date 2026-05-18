import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { History, Search, ChevronDown, ChevronUp, AlertCircle, Code, GitBranch, FileText } from 'lucide-react'
import { useStore } from '../store/useStore'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
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
