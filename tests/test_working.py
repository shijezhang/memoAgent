from memo_agent.memory.working import WorkingMemory


def test_add_and_get_full_context():
    wm = WorkingMemory()
    wm.add("user", "hello")
    wm.add("assistant", "hi there")
    ctx = wm.get_full_context()
    assert len(ctx) == 2
    assert ctx[0] == {"role": "user", "content": "hello"}
    assert ctx[1] == {"role": "assistant", "content": "hi there"}


def test_get_recent():
    wm = WorkingMemory()
    for i in range(5):
        wm.add("user", f"msg {i}")
    recent = wm.get_recent(3)
    assert len(recent) == 3
    assert recent[0]["content"] == "msg 2"
    assert recent[2]["content"] == "msg 4"


def test_get_recent_more_than_available():
    wm = WorkingMemory()
    wm.add("user", "only one")
    recent = wm.get_recent(5)
    assert len(recent) == 1


def test_clear():
    wm = WorkingMemory()
    wm.add("user", "hello")
    wm.clear()
    assert wm.get_full_context() == []


def test_empty_context():
    wm = WorkingMemory()
    assert wm.get_full_context() == []
    assert wm.get_recent(3) == []
