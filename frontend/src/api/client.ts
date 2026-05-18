import axios from 'axios'
import type {
  ChatRequest,
  ChatResponse,
  KnowledgeGraph,
  MemoryStatus,
  ReflectionLogEntry,
  KGNode,
  EntityCreate,
  StatusResponse,
} from './types'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export const chatApi = {
  sendMessage: async (message: string, sessionId?: string): Promise<ChatResponse> => {
    const request: ChatRequest = { message, session_id: sessionId }
    const response = await api.post<ChatResponse>('/chat', request)
    return response.data
  },

  createWebSocket: (onMessage: (text: string) => void, onDone: () => void): WebSocket => {
    const ws = new WebSocket(`${window.location.origin.replace('http', 'ws')}/api/chat/ws`)
    ws.onmessage = (event) => {
      if (event.data === '[DONE]') {
        onDone()
      } else {
        onMessage(event.data)
      }
    }
    return ws
  },
}

export const memoryApi = {
  getStatus: async (): Promise<MemoryStatus> => {
    const response = await api.get<MemoryStatus>('/memory/status')
    return response.data
  },

  clearEpisodic: async (): Promise<StatusResponse> => {
    const response = await api.delete<StatusResponse>('/memory/episodic')
    return response.data
  },
}

export const knowledgeApi = {
  getGraph: async (): Promise<KnowledgeGraph> => {
    const response = await api.get<KnowledgeGraph>('/knowledge/graph')
    return response.data
  },

  getSubgraph: async (entity: string): Promise<KnowledgeGraph> => {
    const response = await api.get<KnowledgeGraph>('/knowledge/subgraph', {
      params: { entity },
    })
    return response.data
  },

  createEntity: async (name: string): Promise<KGNode> => {
    const request: EntityCreate = { name }
    const response = await api.post<KGNode>('/knowledge/entity', request)
    return response.data
  },

  deleteEntity: async (id: string): Promise<StatusResponse> => {
    const response = await api.delete<StatusResponse>(`/knowledge/entity/${id}`)
    return response.data
  },
}

export const reflectionApi = {
  getReflections: async (limit = 50, entity?: string): Promise<ReflectionLogEntry[]> => {
    const response = await api.get<ReflectionLogEntry[]>('/reflections', {
      params: { limit, entity },
    })
    return response.data
  },

  getGuidelines: async (): Promise<KGNode[]> => {
    const response = await api.get<KGNode[]>('/guidelines')
    return response.data
  },
}

export default api
