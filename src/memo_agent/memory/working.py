class WorkingMemory:
    def __init__(self):
        self._messages: list[dict] = []

    def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    def get_recent(self, n: int = 3) -> list[dict]:
        return self._messages[-n:] if n > 0 else []

    def get_full_context(self) -> list[dict]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()
