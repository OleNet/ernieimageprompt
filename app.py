#!/usr/bin/env python3
"""
Discover ERNIE Image Prompts — pure stdlib HTTP server (no Flask needed)
"""
import json, os, math, mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

HOST = '0.0.0.0'
PORT = 8766
GOODCASE_DIR = '/home/anastasia/t2i_result/goodcase'
STATIC_DIR   = os.path.join(os.path.dirname(__file__), 'static')
GALLERY_JSON = os.path.join(GOODCASE_DIR, 'gallery_data.json')
PAGE_SIZE    = 12

with open(GALLERY_JSON, encoding='utf-8') as f:
    GALLERY = json.load(f)

print(f"Loaded {len(GALLERY)} items from gallery_data.json")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, mime):
        with open(path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', len(data))
        self.end_headers()
        try:
            self.wfile.write(data)
        except BrokenPipeError:
            pass

    def log_error(self, fmt, *args):
        pass  # 屏蔽客户端断开的噪音，避免 BrokenPipe 打印堆栈

    def send_404(self):
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        qs     = parse_qs(parsed.query)

        # API
        if path == '/api/images':
            page = int(qs.get('page', ['1'])[0])
            size = int(qs.get('size', [str(PAGE_SIZE)])[0])
            start = (page - 1) * size
            end   = start + size
            items = GALLERY[start:end]
            self.send_json({
                'total':    len(GALLERY),
                'page':     page,
                'size':     size,
                'pages':    math.ceil(len(GALLERY) / size),
                'items':    items,
                'has_more': end < len(GALLERY),
            })
            return

        # Serve image files
        if path.startswith('/images/'):
            filename = os.path.basename(path)
            img_path = os.path.join(GOODCASE_DIR, filename)
            if os.path.isfile(img_path):
                mime, _ = mimetypes.guess_type(img_path)
                self.send_file(img_path, mime or 'image/png')
            else:
                self.send_404()
            return

        # Static files
        if path == '/' or path == '/index.html':
            filepath = os.path.join(STATIC_DIR, 'index.html')
        else:
            filepath = os.path.join(STATIC_DIR, path.lstrip('/'))

        if os.path.isfile(filepath):
            mime, _ = mimetypes.guess_type(filepath)
            self.send_file(filepath, mime or 'text/plain')
        else:
            self.send_404()


if __name__ == '__main__':
    server = HTTPServer((HOST, PORT), Handler)
    ip = os.popen('hostname -i').read().strip().split()[0]
    print(f"\n🟢  Gallery running at  http://{ip}:{PORT}\n")
    server.serve_forever()
