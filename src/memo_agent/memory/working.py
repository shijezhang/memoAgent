class WorkingMemory:
    def __init__(self, max_turns: int = 50):
        self._messages: list[dict] = []
        self._max_turns = max_turns

    def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})
        while len(self._messages) > self._max_turns * 2:
            self._messages.pop(0)

    def get_recent(self, n: int = 3) -> list[dict]:
        return self._messages[-n:] if n > 0 else []

    def get_full_context(self) -> list[dict]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    @property
    def turn_count(self) -> int:
        return len(self._messages) // 2
