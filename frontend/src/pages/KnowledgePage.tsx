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
