import socket
import struct
import json
from dataclasses import dataclass
import cv2
import numpy as np
from .constants import MAX_FRAME_BYTES, MAX_METADATA_BYTES, MAX_PACKET_BYTES


@dataclass(frozen=True)
class FrameMessage:
    """A frame and its original metadata travel together through processing."""

    frame_id: str
    metadata: dict[str, object]
    frame: np.ndarray


def receive_exact(conn: socket.socket, size: int) -> bytearray:
    """Citeste exact size bytes sau semnaleaza deconectarea."""
    data = bytearray()

    while len(data) < size:
        chunk = conn.recv(size - len(data))

        if not chunk:
            raise EOFError("Clientul s-a deconectat")

        data.extend(chunk)

    return data

def receive_frame(conn: socket.socket) -> FrameMessage:
    packet_length = struct.unpack("!I", receive_exact(conn, 4))[0]
    if not 4 < packet_length <= MAX_PACKET_BYTES:
        raise ValueError(f"Lungime pachet invalida: {packet_length}")

    metadata_length = struct.unpack("!I", receive_exact(conn, 4))[0]
    if not 0 < metadata_length <= MAX_METADATA_BYTES or metadata_length > packet_length - 4:
        raise ValueError(f"Lungime metadata invalida: {metadata_length}")

    metadata_bytes = receive_exact(conn, metadata_length)
    try:
        metadata = json.loads(metadata_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Metadata nu este JSON UTF-8 valid") from error

    image_length = packet_length - 4 - metadata_length
    if not 0 < image_length <= MAX_FRAME_BYTES:
        raise ValueError(f"Lungime JPEG invalida: {image_length}")

    if not isinstance(metadata, dict):
        raise ValueError("Metadata trebuie sa fie un obiect JSON")
    frame_id = metadata.get("frame_id")
    if (metadata.get("type") != "frame" or
            not isinstance(frame_id, str) or not frame_id.isdecimal() or
            not 0 < int(frame_id) <= 0xFFFFFFFFFFFFFFFF or
            not isinstance(metadata.get("capture_timestamp"), str) or
            not metadata["capture_timestamp"] or
            not isinstance(metadata.get("camera_id"), str) or
            not metadata["camera_id"] or
            type(metadata.get("width")) is not int or metadata["width"] <= 0 or
            type(metadata.get("height")) is not int or metadata["height"] <= 0):
        raise ValueError("Metadata cadru invalida sau incompleta")

    payload = receive_exact(conn, image_length)
    frame = cv2.imdecode(
        np.frombuffer(payload, dtype=np.uint8),
        cv2.IMREAD_COLOR,
    )

    if frame is None:
        raise ValueError("Datele primite nu reprezinta o imagine valida")
    if frame.shape[1] != metadata["width"] or frame.shape[0] != metadata["height"]:
        raise ValueError("Dimensiunile JPEG nu corespund metadata-ului")

    return FrameMessage(frame_id=frame_id, metadata=metadata, frame=frame)
