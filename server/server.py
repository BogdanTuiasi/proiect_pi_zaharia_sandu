import socket
import cv2
from receiver import receive_frame

def main():
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
                            frame = receive_frame(conn)

                            # Aici vom apela OCR-ul si traducerea.
                            # frame este o imagine OpenCV in format BGR
                            # (albastru pe primul canal, nu RGB).
                            cv2.imshow("Quest camera", frame)

                            if cv2.waitKey(1) == 27:
                                return

                    except (EOFError, OSError, ValueError) as error:
                        print(f"Conexiune inchisa: {error}")
        finally:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()