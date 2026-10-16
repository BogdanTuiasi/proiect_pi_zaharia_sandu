import socket
import struct
import cv2
import numpy as np
from .constants import MAX_FRAME_BYTES as MAX_FRAME_BYTES

def send_exact(conn: socket.socket, data: bytes) -> None:
    """Scrie exact size bytes."""

    while len(data) > 0:
        num_bytes_sent = conn.send(data, len(data))

        if num_bytes_sent == 0:
            raise ConnectionError("Conexiunea s-a terminat.")

        data = data[num_bytes_sent:]

def send_frame(conn: socket.socket, frame: np.ndarray) -> None:
    success, encoded = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 65],
    )
    if not success:
        raise ValueError("Imaginea nu a putut fi codificata")

    payload = encoded.tobytes()
    length = len(payload)
    if not 0 < length <= MAX_FRAME_BYTES:
        raise ValueError("Dimensiune cadru invalida")

    header = struct.pack("!I", len(payload))
    
    send_exact(conn, header)
    send_exact(conn, payload)
