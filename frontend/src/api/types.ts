export interface ChatRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  response: string
  session_id: string
  entities: string[]
  guidelines_used: string[]
  is_reflection: boolean
  guideline?: string
}

export interface ReflectionLogEntry {
  id: string
  rule: string
  source_entities: string[]
  error_context: string
  reflection_prompt: string
  kg_diff: Record<string, unknown>
  timestamp: string
}

export interface KGNode {
  id: string
  type: string
  name?: string
  rule?: string
}

export interface KGEdge {
  source: string
  target: string
  relation: string
}

export interface KnowledgeGraph {
  nodes: KGNode[]
  edges: KGEdge[]
}

export interface MemoryStatus {
  semantic: {
    entities: number
    guidelines: number
  }
  episodic: {
    conversations: number
  }
  working: {
    turns: number
  }
}

export interface EntityCreate {
  name: string
}

export interface StatusResponse {
  status: string
}
