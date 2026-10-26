import socket
import struct
import json
import cv2
import numpy as np
from .constants import MAX_FRAME_BYTES, MAX_METADATA_BYTES, MAX_PACKET_BYTES
from .receiver import FrameMessage

def send_exact(conn: socket.socket, data: bytes) -> None:
    """Scrie exact size bytes."""

    while len(data) > 0:
        num_bytes_sent = conn.send(data)

        if num_bytes_sent == 0:
            raise ConnectionError("Conexiunea s-a terminat.")

        data = data[num_bytes_sent:]

def send_frame(conn: socket.socket, message: FrameMessage) -> None:
    if message.metadata.get("type") != "processing_result":
        raise ValueError("Raspunsul trebuie sa aiba type='processing_result'")
    if message.metadata.get("frame_id") != message.frame_id:
        raise ValueError("ID-ul cadrului lipseste din metadata rezultatului")

    success, encoded = cv2.imencode(
        ".jpg",
        message.frame,
        [cv2.IMWRITE_JPEG_QUALITY, 65],
    )
    if not success:
        raise ValueError("Imaginea nu a putut fi codificata")

    payload = encoded.tobytes()
    length = len(payload)
    if not 0 < length <= MAX_FRAME_BYTES:
        raise ValueError("Dimensiune cadru invalida")

    metadata_bytes = json.dumps(
        message.metadata,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    metadata_length = len(metadata_bytes)
    if not 0 < metadata_length <= MAX_METADATA_BYTES:
        raise ValueError("Dimensiune metadata invalida")

    packet_length = 4 + metadata_length + length
    if packet_length > MAX_PACKET_BYTES:
        raise ValueError("Dimensiune pachet invalida")

    header = struct.pack("!II", packet_length, metadata_length)
    
    send_exact(conn, header)
    send_exact(conn, metadata_bytes)
    send_exact(conn, payload)
