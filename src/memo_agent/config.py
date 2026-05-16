from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

@dataclass
class Config:
    llm_model: str = "claude-sonnet-4-20250514"
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
    max_context_tokens: int = 160000
    context_usage_ratio: float = 0.8
    guideline_max_tokens: int = 0  # 0 = no limit
    subgraph_max_tokens: int = 1000
    episodic_max_tokens: int = 1500
    episodic_top_k: int = 3
    reflection_recent_turns: int = 3

    def __post_init__(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.kg_dir.mkdir(parents=True, exist_ok=True)
