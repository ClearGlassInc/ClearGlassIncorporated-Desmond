import pytest

from clearglassinc_sdk.memory import Memory, Message
from clearglassinc_sdk.sessions import (
    FileSessionStore,
    InMemorySessionStore,
    load_into_memory,
    save_from_memory,
)


def sample_messages() -> list[Message]:
    return [
        Message(role="user", content="hello"),
        Message(role="assistant", content="hi there"),
        Message(role="tool", content="pong", name="ping", tool_call_id="c1"),
    ]


@pytest.fixture(params=["memory", "file"])
def store(request, tmp_path):
    if request.param == "memory":
        return InMemorySessionStore()
    return FileSessionStore(directory=str(tmp_path / "sessions"))


def test_save_and_load_roundtrip(store):
    store.save("s1", sample_messages())
    loaded = store.load("s1")

    assert [m.role for m in loaded] == ["user", "assistant", "tool"]
    assert loaded[2].name == "ping"
    assert loaded[2].tool_call_id == "c1"


def test_load_unknown_session_returns_empty(store):
    assert store.load("does-not-exist") == []


def test_delete_removes_session(store):
    store.save("s1", sample_messages())
    store.delete("s1")
    assert store.load("s1") == []


def test_delete_is_idempotent(store):
    store.delete("never-existed")  # must not raise


def test_list_sessions(store):
    store.save("alpha", sample_messages())
    store.save("beta", sample_messages())
    assert store.list_sessions() == ["alpha", "beta"]


def test_save_overwrites_existing_session(store):
    store.save("s1", sample_messages())
    store.save("s1", [Message(role="user", content="replaced")])
    loaded = store.load("s1")
    assert len(loaded) == 1
    assert loaded[0].content == "replaced"


def test_file_store_neutralizes_path_traversal(tmp_path):
    """A traversal-shaped id is sanitized to a flat name, never escaping the
    session directory."""
    directory = tmp_path / "sessions"
    store = FileSessionStore(directory=str(directory))

    store.save("../../etc/passwd", sample_messages())

    written = list(directory.iterdir())
    assert [path.name for path in written] == ["etcpasswd.json"]
    assert not (tmp_path.parent / "etc").exists()


def test_file_store_rejects_session_id_with_no_safe_characters(tmp_path):
    store = FileSessionStore(directory=str(tmp_path))
    with pytest.raises(ValueError):
        store.save("///...", sample_messages())


def test_file_store_sanitizes_path_separators(tmp_path):
    store = FileSessionStore(directory=str(tmp_path))
    store.save("a/b", [Message(role="user", content="x")])
    # The slash is stripped rather than creating a nested directory.
    assert store.list_sessions() == ["ab"]


def test_load_into_memory_replaces_history(store):
    store.save("s1", sample_messages())
    memory = Memory()
    memory.add_user("stale content")

    load_into_memory(store, "s1", memory)

    assert [m.content for m in memory.history()] == ["hello", "hi there", "pong"]


def test_save_from_memory_persists_history(store):
    memory = Memory()
    memory.add_user("first")
    memory.add_assistant("second")

    save_from_memory(store, "s1", memory)

    assert [m.content for m in store.load("s1")] == ["first", "second"]
