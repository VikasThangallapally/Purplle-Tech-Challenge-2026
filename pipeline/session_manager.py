from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class Session:
    visitor_id: int
    first_seen_ms: float
    last_seen_ms: float
    first_frame: int
    last_frame: int
    active: bool = True
    metadata: dict = field(default_factory=dict)
    # track whether this session existed at video initialization
    is_initial: bool = False
    # whether an ENTRY event has been emitted for this session
    has_entry_event: bool = False


class SessionManager:
    def __init__(self, exit_frame_threshold: int = 30):
        # frame threshold after which a missing track is considered exited
        self.exit_frame_threshold = int(exit_frame_threshold)
        # key by (visitor_id, camera_id)
        self._sessions: Dict[Tuple[int, str], Session] = {}

    def touch(self, visitor_id: int, frame_index: int, timestamp_ms: float, metadata: Optional[dict] = None, is_initial: bool = False, camera_id: str = "") -> Session:
        """Mark a visitor seen at a given frame/timestamp. Create session if new."""
        metadata = metadata or {}
        key = (int(visitor_id), str(camera_id))
        if key in self._sessions:
            s = self._sessions[key]
            s.last_seen_ms = timestamp_ms
            s.last_frame = frame_index
            s.active = True
            s.metadata.update(metadata)
            return s
        s = Session(visitor_id=int(visitor_id), first_seen_ms=timestamp_ms, last_seen_ms=timestamp_ms, first_frame=frame_index, last_frame=frame_index, active=True, metadata=metadata, is_initial=bool(is_initial), has_entry_event=False)
        self._sessions[key] = s
        return s

    def maybe_exit(self, visitor_id: int, current_frame_index: int, camera_id: str = "") -> Optional[Session]:
        """If visitor has been missing for exit_frame_threshold frames, mark as exited and return session."""
        key = (int(visitor_id), str(camera_id))
        s = self._sessions.get(key)
        if s is None:
            return None
        if not s.active:
            return None
        # if gap in frames larger than threshold
        if current_frame_index - s.last_frame > self.exit_frame_threshold:
            s.active = False
            return s
        return None

    def active_sessions(self) -> Dict[int, Session]:
        return {k: v for k, v in self._sessions.items() if v.active}

    def all_sessions(self) -> Dict[int, Session]:
        return dict(self._sessions)
