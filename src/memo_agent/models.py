from dataclasses import dataclass, field


@dataclass
class Guideline:
    rule: str
    source_entities: list[str] = field(default_factory=list)
    timestamp: str = ""
