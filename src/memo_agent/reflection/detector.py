from typing import Optional

from memo_agent.config import Config


class ReflectionDetector:
    def __init__(self, config: Config):
        self._keywords = config.negation_keywords
        self._commands = config.reflection_commands

    def check(self, user_input: str) -> bool:
        stripped = user_input.strip()
        if stripped in self._commands:
            return True
        for kw in self._keywords:
            if kw in stripped:
                return True
        return False

    def extract_correction(self, user_input: str) -> Optional[dict]:
        if not self.check(user_input):
            return None
        stripped = user_input.strip()
        hint = stripped
        for kw in self._keywords:
            hint = hint.replace(kw, "", 1)
        hint = hint.strip().lstrip(",，、").strip()
        return {"trigger": stripped, "hint": hint if hint else stripped}
