import socket
import cv2
from .receiver import FrameMessage, receive_frame
from .sender import send_frame

def run_server(process_frame):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 5000))
        server.listen(1)

        print("Server pornit pe portul 5000")

        try:
            while True:
                print("Astept conexiunea de la Quest...")
                conn, address = server.accept()
                print(f"Conectat: {address}")

                with conn:
                    conn.settimeout(15)

                    try:
                        while True:
                            # metadata include frame ID si contextul imaginii.
                            # frame este o imagine OpenCV in format BGR
                            # (albastru pe primul canal, nu RGB).
                            frame_message = receive_frame(conn)
                            original_frame_id = frame_message.frame_id
                            processed_frame = process_frame(frame_message.frame)
                            result_message = FrameMessage(
                                frame_id=original_frame_id,
                                metadata={
                                    **frame_message.metadata,
                                    "type": "processing_result",
                                },
                                frame=processed_frame,
                            )
                            if result_message.frame_id != original_frame_id:
                                raise ValueError("ID-ul cadrului s-a schimbat in timpul procesarii")

                            send_frame(conn, result_message)
                            cv2.imshow("Quest camera", result_message.frame)

                            if cv2.waitKey(1) == 27:
                                return

                    except (EOFError, OSError, ValueError) as error:
                        print(f"Conexiune inchisa: {error}")
        finally:
            cv2.destroyAllWindows()
