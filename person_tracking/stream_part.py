import cv2
from http.server import BaseHTTPRequestHandler


class CamHandler(BaseHTTPRequestHandler):
    def __init__(self, queue, flag, *args, **kwargs):
        self.queue = queue
        self.flag = flag
        super().__init__(*args, **kwargs)

    def put_image(self, frame):
        self.queue.append(frame)

    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def _html(self, message):
        content = f"<html><body><h1>{message}</h1></body></html>"
        return content.encode("utf8")

    def do_GET(self):
        if self.path.endswith("refresh"):
            self.flag["REFRESH"] = True
            self._set_headers()
            self.wfile.write(self._html("OK"))
            return

        elif self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header(
                'Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()

            try:
                while True:
                    while len(self.queue) == 0:
                        pass
                    frame = self.queue.popleft()

                    ret, jpeg = cv2.imencode('.jpg', frame)
                    self.wfile.write("--jpgboundary\r\n".encode())
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', str(len(jpeg)))
                    self.end_headers()
                    self.wfile.write(jpeg)
                    self.wfile.write('\r\n'.encode())

            except Exception as e:
                print(str(e))

            return
        else:
            self.send_error(404, 'File Not Found: %s' % self.path)
