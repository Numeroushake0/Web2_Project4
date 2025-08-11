import http.server
import socketserver
import socket
import threading
import urllib.parse
import json
from datetime import datetime
import os

HTTP_PORT = 3000
SOCKET_PORT = 5000
BASE_DIR = os.path.join(os.path.dirname(__file__), "front-init", "front-init")
STORAGE_FILE = os.path.join(BASE_DIR, "storage", "data.json")


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "index.html"
        elif self.path == "/message":
            self.path = "message.html"

        file_path = os.path.join(BASE_DIR, self.path.lstrip("/"))
        if os.path.isfile(file_path):
            self.send_response(200)
            if file_path.endswith(".css"):
                self.send_header("Content-type", "text/css")
            elif file_path.endswith(".png"):
                self.send_header("Content-type", "image/png")
            elif file_path.endswith(".html"):
                self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error_page()

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode("utf-8")
            form_data = urllib.parse.parse_qs(post_data)

            username = form_data.get("username", [""])[0]
            message = form_data.get("message", [""])[0]

            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = json.dumps({"username": username, "message": message})
            udp_socket.sendto(data.encode("utf-8"), ("localhost", SOCKET_PORT))
            udp_socket.close()

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>Повідомлення надіслано!</h1>")
        else:
            self.send_error_page()

    def send_error_page(self):
        error_path = os.path.join(BASE_DIR, "error.html")
        self.send_response(404)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        with open(error_path, "rb") as f:
            self.wfile.write(f.read())


def run_http_server():
    os.chdir(BASE_DIR)
    with socketserver.TCPServer(("", HTTP_PORT), MyHandler) as httpd:
        print(f"HTTP сервер запущено на порту {HTTP_PORT}")
        httpd.serve_forever()


def run_socket_server():
    if not os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "w") as f:
            json.dump({}, f)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", SOCKET_PORT))
    print(f"UDP Socket сервер запущено на порту {SOCKET_PORT}")

    while True:
        data, _ = sock.recvfrom(1024)
        message_dict = json.loads(data.decode("utf-8"))
        timestamp = str(datetime.now())

        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)

        messages[timestamp] = message_dict

        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    socket_thread = threading.Thread(target=run_socket_server, daemon=True)

    http_thread.start()
    socket_thread.start()

    http_thread.join()
    socket_thread.join()
