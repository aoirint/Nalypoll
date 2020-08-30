import time
import socket

def open_socket(
    host: str,
    port: int,
):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, port))
        sock.listen(1)

        sock.accept()

def wait_socket(
    host: str,
    port: int,
    interval: float = 1.0
):
    running = True
    while running:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.settimeout(interval)
                sock.connect((host, port))

                running = False
            except ConnectionRefusedError:
                pass
            except socket.timeout:
                pass

            time.sleep(0.1)
