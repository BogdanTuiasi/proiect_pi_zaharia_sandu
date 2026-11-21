import socket
import cv2
from .receiver import receive_frame
from .sender import send_config, send_processing_result

def run_server(
    process_frame,
    fps: int = 20,
    jpeg_quality: int = 65,
    target_language: str = "ro",
    reset_process_state=None,
):
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
                    if reset_process_state is not None:
                        reset_process_state()

                    try:
                        send_config(conn, fps=fps, jpeg_quality=jpeg_quality, target_language=target_language)
                        while True:
                            # metadata include frame ID si contextul imaginii.
                            # frame este o imagine OpenCV in format BGR
                            # (albastru pe primul canal, nu RGB).
                            frame_message = receive_frame(conn)
                            regions = process_frame(frame_message.frame)
                            result_metadata = {
                                **frame_message.metadata,
                                "type": "processing_result",
                                "regions": regions,
                            }

                            send_processing_result(conn, result_metadata)
                            cv2.imshow("Quest camera", frame_message.frame)

                            if cv2.waitKey(1) == 27:
                                return

                    except (EOFError, OSError, ValueError) as error:
                        print(f"Conexiune inchisa: {error}")
        finally:
            cv2.destroyAllWindows()
