import { create } from 'zustand'
import type { MemoryStatus, KnowledgeGraph, ReflectionLogEntry } from '../api/types'
import { memoryApi, knowledgeApi, reflectionApi } from '../api/client'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  guidelines?: string[]
  isReflection?: boolean
}

interface Store {
  // Chat state
  messages: Message[]
  sessionId: string
  isLoading: boolean

  // Memory state
  memoryStatus: MemoryStatus | null

  // Knowledge graph state
  knowledgeGraph: KnowledgeGraph | null
  selectedNode: string | null

  // Reflection state
  reflections: ReflectionLogEntry[]

  // Actions
  addMessage: (message: Omit<Message, 'id'> & { id?: string }) => void
  setSessionId: (id: string) => void
  setLoading: (loading: boolean) => void
  clearMessages: () => void

  fetchMemoryStatus: () => Promise<void>
  fetchKnowledgeGraph: () => Promise<void>
  setSelectedNode: (nodeId: string | null) => void

  fetchReflections: (limit?: number, entity?: string) => Promise<void>
}

export const useStore = create<Store>((set) => ({
  // Initial state
  messages: [],
  sessionId: '',
  isLoading: false,
  memoryStatus: null,
  knowledgeGraph: null,
  selectedNode: null,
  reflections: [],

  // Chat actions
  addMessage: (message) => {
    const messageWithId = {
      ...message,
      id: message.id || `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    }
    set((state) => ({ messages: [...state.messages, messageWithId] }))
  },

  setSessionId: (id) => set({ sessionId: id }),

  setLoading: (loading) => set({ isLoading: loading }),

  clearMessages: () => set({ messages: [], sessionId: '' }),

  // Memory actions
  fetchMemoryStatus: async () => {
    try {
      const status = await memoryApi.getStatus()
      set({ memoryStatus: status })
    } catch (error) {
      console.error('Failed to fetch memory status:', error)
    }
  },

  // Knowledge graph actions
  fetchKnowledgeGraph: async () => {
    try {
      const graph = await knowledgeApi.getGraph()
      set({ knowledgeGraph: graph })
    } catch (error) {
      console.error('Failed to fetch knowledge graph:', error)
    }
  },

  setSelectedNode: (nodeId) => set({ selectedNode: nodeId }),

  // Reflection actions
  fetchReflections: async (limit = 50, entity?: string) => {
    try {
      const reflections = await reflectionApi.getReflections(limit, entity)
      set({ reflections })
    } catch (error) {
      console.error('Failed to fetch reflections:', error)
    }
  },
}))

export default useStore
