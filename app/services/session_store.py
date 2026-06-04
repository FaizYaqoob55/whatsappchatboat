import json
import os
from pathlib import Path
from threading import RLock
from typing import Dict

from loguru import logger
from pydantic import BaseModel

from app.models.schemas import ChatSession
from app.core.config import get_settings

class SessionStore:
    """Simple JSON‑backed session store.

    - Loads existing sessions from the JSON file defined by ``settings.session_store_path``.
    - Persists sessions after any modification.
    - Thread‑safe via an ``RLock`` because FastAPI can run concurrent requests.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._file_path = Path(self._settings.session_store_path)
        # Ensure the parent directory exists
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._sessions: Dict[str, ChatSession] = {}
        self._load()

    def _load(self) -> None:
        """Load sessions from JSON if the file exists; otherwise start empty."""
        if self._file_path.is_file():
            try:
                with self._file_path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                # Re‑create ChatSession objects from the stored dicts
                for phone, data in raw.items():
                    self._sessions[phone] = ChatSession(**data)
            except Exception as e:
                logger.error(f"Failed to load session store: {e}")
                self._sessions = {}
        else:
            self._sessions = {}

    def _persist(self) -> None:
        """Write the current session dict to disk in a safe atomic fashion."""
        with self._lock:
            tmp_path = self._file_path.with_suffix('.tmp')
            # Serialise using the Pydantic ``dict`` method for each session
            data = {phone: session.dict() for phone, session in self._sessions.items()}
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp_path.replace(self._file_path)

    def get(self, phone: str) -> ChatSession:
        """Retrieve an existing session or create a fresh one if missing."""
        with self._lock:
            if phone not in self._sessions:
                self._sessions[phone] = ChatSession(phone=phone)
                self._persist()
            return self._sessions[phone]

    def delete(self, phone: str) -> None:
        """Remove a session from the store and persist the change."""
        with self._lock:
            if phone in self._sessions:
                del self._sessions[phone]
                self._persist()

    def all_sessions(self) -> Dict[str, ChatSession]:
        """Return a shallow copy of the internal session mapping (read‑only)."""
        return dict(self._sessions)

    # Compatibility helpers used by existing chatbot code
    def get_or_create(self, phone: str) -> ChatSession:
        """Alias for ``get`` to match previous ``get_or_create_session`` semantics."""
        return self.get(phone)

    def clear(self, phone: str) -> None:
        """Alias for ``delete`` used by ``clear_session`` helper."""
        self.delete(phone)
