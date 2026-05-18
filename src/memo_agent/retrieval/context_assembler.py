import logging
from typing import List, Tuple

from memo_agent.memory.working import WorkingMemory
from memo_agent.memory.episodic import EpisodicMemory
from memo_agent.memory.semantic import SemanticMemory
from memo_agent.retrieval.entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """你是一个学术研究助手，具备长期记忆和反思能力。

核心行为：
- 回答学术问题时，优先参考上下文中的 Guidelines（已验证的规则）
- 如果 Guidelines 与你的判断冲突，以 Guidelines 为准
- 当用户纠正你的回答时，你会反思并沉淀新的 Guideline
- 回复语言与用户输入语言一致
- 回复应当准确、结构化，适当引用来源

上下文结构说明：
[Guidelines] - 从过去反思中沉淀的规则，最高优先级
[Knowledge]  - 知识图谱中的实体关系
[History]    - 相关的历史对话
[Current]    - 当前会话内容
"""


class ContextAssembler:
    def __init__(
        self,
        entity_extractor: EntityExtractor,
        max_subgraph_tokens: int = 1000,
        max_episodic_tokens: int = 1500,
        max_context_tokens: int = 128000,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        self._entity_extractor = entity_extractor
        self._max_subgraph_tokens = max_subgraph_tokens
        self._max_episodic_tokens = max_episodic_tokens
        self._max_context_tokens = int(max_context_tokens * 0.8)
        self._system_prompt = system_prompt

    def assemble(self, user_input: str, working: WorkingMemory,
                 episodic: EpisodicMemory, semantic: SemanticMemory) -> str:
        entities = self._entity_extractor.extract(user_input)
        sections: List[Tuple[str, str]] = []

        # System Prompt - always first
        sections.append(("system", self._system_prompt))

        # Priority 1: Guidelines — never truncated
        guidelines = []
        if entities:
            for entity in entities:
                guidelines.extend(semantic.get_guidelines_for(entity))

        if guidelines:
            rule_lines = "\n".join(f"- {g}" for g in guidelines)
            sections.append(("guidelines", f"【学术审查规则 - 你必须严格遵守】\n{rule_lines}"))

        # Priority 2: Knowledge subgraph — truncate to max_subgraph_tokens
        knowledge = ""
        if entities:
            subgraph = semantic.get_subgraph(entities, depth=1)
            if subgraph["nodes"]:
                parts = []
                for node in subgraph["nodes"]:
                    parts.append(f"  {node['name']} ({node.get('entity_type', node.get('type', ''))})")
                for edge in subgraph["edges"]:
                    parts.append(f"  {edge['source']} --[{edge['relation']}]--> {edge['target']}")
                knowledge = "\n".join(parts)
        if knowledge:
            knowledge = self._truncate(knowledge, self._max_subgraph_tokens)
            sections.append(("subgraph", f"【相关知识】\n{knowledge}"))

        # Priority 3: Episodic memory — truncate to max_episodic_tokens
        episodic_results = episodic.search(user_input, top_k=3)
        if episodic_results:
            history_parts = []
            for item in episodic_results:
                cid = item["metadata"].get("conversation_id", "unknown")
                ts = item["metadata"].get("timestamp", "unknown")
                history_parts.append(f"[{cid} @ {ts}] {item['content']}")
            history_text = "\n".join(history_parts)
            history_text = self._truncate(history_text, self._max_episodic_tokens)
            sections.append(("episodic", f"【相关历史讨论】\n{history_text}"))

        # Priority 4: Current conversation — truncate oldest turns first
        current_ctx = working.get_full_context()
        if current_ctx:
            conv_lines = [f"{msg['role']}: {msg['content']}" for msg in current_ctx]
            conv_text = self._truncate_list(conv_lines, self._remaining_budget(sections))
            if conv_text:
                sections.append(("context", f"【当前对话】\n{conv_text}"))

        sections.append(("user", f"【用户最新输入】\n{user_input}"))

        return "\n\n".join(text for _, text in sections)

    @staticmethod
    def _truncate(text: str, max_tokens: int) -> str:
        # Rough estimate: 1 token ≈ 1.5 chars for mixed CJK/English
        max_chars = int(max_tokens * 1.5)
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    @staticmethod
    def _truncate_list(lines: List[str], max_tokens: int) -> str:
        max_chars = int(max_tokens * 1.5)
        result_chars = 0
        kept: List[str] = []
        for line in lines:
            if result_chars + len(line) > max_chars:
                break
            kept.append(line)
            result_chars += len(line)
        return "\n".join(kept)

    def _remaining_budget(self, sections: List[Tuple[str, str]]) -> int:
        used = sum(int(len(text) / 1.5) for _, text in sections)
        return max(self._max_context_tokens - used, 2000)
