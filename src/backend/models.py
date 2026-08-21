import time
import threading
from typing import List, Dict, Any, Optional

class MessageStore:
    def __init__(self, initial_messages: Optional[List[Dict[str, Any]]] = None):
        self._lock = threading.Lock()
        self._messages: List[Dict[str, Any]] = []
        self._next_id = 1
        self._channels = ["general", "distributed-systems", "announcements", "random"]
        
        if initial_messages:
            for msg in initial_messages:
                self.add_message(msg.get("sender", "System"), msg.get("content", ""), msg.get("channel", "general"))
        else:
            self._seed_default_messages()

    def _seed_default_messages(self):
        default_seed = [
            ("Alice", "Welcome to the distributed messaging cluster!", "general"),
            ("Bob", "Sys2, Sys3, and Sys4 backends are online.", "distributed-systems"),
            ("Charlie", "Round-robin load balancing active on Sys1.", "announcements"),
        ]
        for sender, content, channel in default_seed:
            self.add_message(sender, content, channel)

    def add_message(self, sender: str, content: str, channel: str = "general") -> Dict[str, Any]:
        with self._lock:
            msg = {
                "id": self._next_id,
                "sender": str(sender),
                "content": str(content),
                "channel": str(channel),
                "timestamp": time.time(),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            self._next_id += 1
            self._messages.append(msg)
            if channel not in self._channels:
                self._channels.append(channel)
            return msg

    def get_messages(self, channel: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            if channel:
                filtered = [m for m in self._messages if m.get("channel") == channel]
                return filtered[-limit:]
            return self._messages[-limit:]

    def get_message_by_id(self, message_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            for m in self._messages:
                if m.get("id") == message_id:
                    return dict(m)
            return None

    def get_channels(self) -> List[str]:
        with self._lock:
            return list(self._channels)

    def count(self) -> int:
        with self._lock:
            return len(self._messages)
