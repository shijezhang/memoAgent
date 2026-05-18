import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

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


@dataclass
class Config:
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")
    chroma_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "chroma")
    kg_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "kg")
    kg_file: Path = field(default_factory=lambda: BASE_DIR / "data" / "kg" / "semantic.json")
    reflection_log: Path = field(default_factory=lambda: BASE_DIR / "data" / "reflection_log.jsonl")
    negation_keywords: list[str] = field(default_factory=lambda: [
        "不对", "错了", "不是这样的", "搞反了", "修改学术假设",
        "不正确", "你说错了", "搞错了", "反了",
    ])
    reflection_commands: list[str] = field(default_factory=lambda: [
        "/reflect", "/纠错",
    ])
    max_context_tokens: int = 64000
    context_usage_ratio: float = 0.8
    guideline_max_tokens: int = 0
    subgraph_max_tokens: int = 1000
    episodic_max_tokens: int = 1500
    episodic_top_k: int = 3
    reflection_recent_turns: int = 3

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: list = field(default_factory=lambda: ["http://localhost:3000"])

    # System Prompt
    system_prompt_template: str = DEFAULT_SYSTEM_PROMPT

    # LLM 重试
    llm_max_retries: int = 3
    llm_retry_base_delay: float = 1.0

    # Working Memory 限制
    working_memory_max_turns: int = 50

    def __post_init__(self):
        self.llm_api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.kg_dir.mkdir(parents=True, exist_ok=True)
