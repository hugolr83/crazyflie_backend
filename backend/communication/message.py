from __future__ import annotations

import struct
from dataclasses import dataclass


@dataclass
class Message:
    x: int
    y: int
    z: int

    @classmethod
    def from_bytes(cls, data: bytes) -> Message:
        x, y, z = struct.unpack("<fff", data)
        return cls(x, y, z)

    def serialize(self) -> bytes:
        return struct.pack("<fff", self.x, self.y, self.z)
