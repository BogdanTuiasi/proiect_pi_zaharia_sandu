import socket
import struct
import cv2
import numpy as np
from .constants import MAX_FRAME_BYTES as MAX_FRAME_BYTES

def receive_exact(conn: socket.socket, size: int) -> bytearray:
    """Citeste exact size bytes sau semnaleaza deconectarea."""
    data = bytearray()

    while len(data) < size:
        chunk = conn.recv(size - len(data))

        if not chunk:
            raise EOFError("Clientul s-a deconectat")

        data.extend(chunk)

    return data

def receive_frame(conn: socket.socket) -> np.ndarray:
    header = receive_exact(conn, 4)
    length = struct.unpack("!I", header)[0] # I = integer, ! = big-endian

    if not 0 < length <= MAX_FRAME_BYTES:
        raise ValueError(f"Lungime cadru invalida: {length}")

    payload = receive_exact(conn, length)
    frame = cv2.imdecode(
        np.frombuffer(payload, dtype=np.uint8),
        cv2.IMREAD_COLOR,
    )

    if frame is None:
        raise ValueError("Datele primite nu reprezinta o imagine valida")

    return frame
