"""Session persistence: save and resume an agent's conversation across runs.

A `SessionStore` holds serialized `Message` history keyed by session id, so a
long-running assistant survives process restarts (and so a web server can
serve many concurrent conversations from one `Agent` definition).
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Protocol

from clearglassinc_sdk.memory import Memory, Message


def _message_to_dict(message: Message) -> dict[str, Any]:
    return {
        "role": message.role,
        "content": message.content,
        "name": message.name,
        "tool_call_id": message.tool_call_id,
        "tool_calls": message.tool_calls,
    }


def _message_from_dict(data: dict[str, Any]) -> Message:
    return Message(
        role=data["role"],
        content=data.get("content", ""),
        name=data.get("name"),
        tool_call_id=data.get("tool_call_id"),
        tool_calls=data.get("tool_calls"),
    )


class SessionStore(Protocol):
    """Persist and retrieve conversation history by session id."""

    def save(self, session_id: str, messages: list[Message]) -> None: ...

    def load(self, session_id: str) -> list[Message]: ...

    def delete(self, session_id: str) -> None: ...

    def list_sessions(self) -> list[str]: ...


@dataclass
class InMemorySessionStore:
    """Process-local session store. Fine for tests and single-process apps."""

    _sessions: dict[str, list[Message]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def save(self, session_id: str, messages: list[Message]) -> None:
        with self._lock:
            self._sessions[session_id] = list(messages)

    def load(self, session_id: str) -> list[Message]:
        with self._lock:
            return list(self._sessions.get(session_id, []))

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def list_sessions(self) -> list[str]:
        with self._lock:
            return sorted(self._sessions)


@dataclass
class FileSessionStore:
    """Durable JSON-file-per-session store — no database required.

    Writes go through a temp file + atomic rename so a crash mid-write can't
    leave a half-written session on disk.
    """

    directory: str
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        os.makedirs(self.directory, exist_ok=True)

    def _path(self, session_id: str) -> str:
        safe = "".join(char for char in session_id if char.isalnum() or char in "-_")
        if not safe:
            raise ValueError(f"session id {session_id!r} has no filesystem-safe characters")
        root = os.path.realpath(self.directory)
        path = os.path.realpath(os.path.join(root, f"{safe}.json"))
        # The filter above already drops every separator and dot, so `safe` cannot
        # describe a parent directory. Re-check the resolved path anyway: this is the
        # boundary that must hold even if that filter is ever loosened, and it also
        # refuses a session file symlinked out of the store.
        if os.path.dirname(path) != root:
            raise ValueError(f"session id {session_id!r} escapes the session directory")
        return path

    def save(self, session_id: str, messages: list[Message]) -> None:
        path = self._path(session_id)
        payload = {"session_id": session_id, "messages": [_message_to_dict(m) for m in messages]}
        with self._lock:
            tmp_path = f"{path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            os.replace(tmp_path, path)

    def load(self, session_id: str) -> list[Message]:
        path = self._path(session_id)
        with self._lock:
            if not os.path.exists(path):
                return []
            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
        return [_message_from_dict(item) for item in payload.get("messages", [])]

    def delete(self, session_id: str) -> None:
        path = self._path(session_id)
        with self._lock:
            if os.path.exists(path):
                os.remove(path)

    def list_sessions(self) -> list[str]:
        with self._lock:
            names = [name for name in os.listdir(self.directory) if name.endswith(".json")]
        return sorted(name[: -len(".json")] for name in names)


def load_into_memory(store: SessionStore, session_id: str, memory: Memory) -> Memory:
    """Replace `memory`'s short-term history with the stored session."""
    memory.clear()
    for message in store.load(session_id):
        memory.add(message)
    return memory


def save_from_memory(store: SessionStore, session_id: str, memory: Memory) -> None:
    """Persist `memory`'s current short-term history under `session_id`."""
    store.save(session_id, memory.history())
