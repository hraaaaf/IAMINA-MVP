import http.client
import http.server
import os
from pathlib import Path

root = Path(os.environ['STATIC_ROOT'])


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(root), **kwargs)

    def _proxy(self):
        length = int(self.headers.get('content-length', '0'))
        body = self.rfile.read(length) if length else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {'host', 'content-length', 'connection'}
        }
        connection = http.client.HTTPConnection('127.0.0.1', 8000, timeout=45)
        connection.request(self.command, self.path, body=body, headers=headers)
        response = connection.getresponse()
        data = response.read()
        self.send_response(response.status)
        for key, value in response.getheaders():
            if key.lower() not in {'content-length', 'transfer-encoding', 'connection'}:
                self.send_header(key, value)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        connection.close()

    def do_GET(self):
        return self._proxy() if self.path.startswith('/api/') else super().do_GET()

    def do_POST(self):
        return self._proxy() if self.path.startswith('/api/') else self.send_error(404)

    def do_PATCH(self):
        return self._proxy() if self.path.startswith('/api/') else self.send_error(404)

    def do_DELETE(self):
        return self._proxy() if self.path.startswith('/api/') else self.send_error(404)

    def log_message(self, *args):
        pass


http.server.ThreadingHTTPServer(('127.0.0.1', 7358), Handler).serve_forever()
