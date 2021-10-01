from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Message:
    uuid: str
    data: bytes
