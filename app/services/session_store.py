import json
from pathlib import Path
from threading import RLock
from typing import Dict

from loguru import logger

from app.models.schemas import ChatSession
from app.core.config import get_settings


class SessionStore:
    """JSON-backed persistent session store for CareDesk WhatsApp chatbot.

    - Loads sessions from a JSON file on startup.
    - Persists sessions to disk after every modification (new session or message save).
    - Thread-safe via RLock — FastAPI may handle concurrent requests.
    - Atomic writes (.tmp → rename) prevent file corruption.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._file_path = Path(self._settings.session_store_path)
        # Ensure parent directory exists (e.g. data/)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._sessions: Dict[str, ChatSession] = {}
        self._load()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load sessions from JSON file on startup. Start empty if file missing."""
        if self._file_path.is_file():
            try:
                with self._file_path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                for phone, data in raw.items():
                    self._sessions[phone] = ChatSession(**data)
                logger.info(f"SessionStore loaded {len(self._sessions)} session(s) from disk.")
            except Exception as e:
                logger.error(f"Failed to load session store: {e}. Starting fresh.")
                self._sessions = {}
        else:
            self._sessions = {}

    def _persist(self) -> None:
        """Atomically write all sessions to disk. Called inside lock."""
        try:
            tmp_path = self._file_path.with_suffix(".tmp")
            # Pydantic v2 uses model_dump(); v1 uses dict() — support both
            data = {}
            for phone, session in self._sessions.items():
                try:
                    data[phone] = session.model_dump()   # Pydantic v2
                except AttributeError:
                    data[phone] = session.dict()          # Pydantic v1 fallback
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp_path.replace(self._file_path)
        except Exception as e:
            logger.error(f"Failed to persist session store: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, phone: str) -> ChatSession:
        """Get existing session or create a new one. Persists if newly created."""
        with self._lock:
            if phone not in self._sessions:
                self._sessions[phone] = ChatSession(phone=phone)
                logger.debug(f"New session created | phone={phone}")
                self._persist()
            return self._sessions[phone]

    def save(self, phone: str) -> None:
        """Persist the current state of an existing session to disk.

        Call this after calling session.add_message() to ensure messages
        are not lost across process restarts.
        """
        with self._lock:
            if phone in self._sessions:
                self._persist()
            else:
                logger.warning(f"save() called for unknown phone={phone} — skipping.")

    def delete(self, phone: str) -> None:
        """Remove a session and persist the change."""
        with self._lock:
            if phone in self._sessions:
                del self._sessions[phone]
                self._persist()
                logger.debug(f"Session deleted | phone={phone}")

    def all_sessions(self) -> Dict[str, ChatSession]:
        """Return a shallow copy of all sessions (read-only view)."""
        with self._lock:
            return dict(self._sessions)

    def session_count(self) -> int:
        """Return total number of active sessions."""
        with self._lock:
            return len(self._sessions)

    # ── Compatibility aliases ─────────────────────────────────────────────────

    def get_or_create(self, phone: str) -> ChatSession:
        """Alias for get() — backward compatibility."""
        return self.get(phone)

    def clear(self, phone: str) -> None:
        """Alias for delete() — backward compatibility."""
        self.delete(phone)
