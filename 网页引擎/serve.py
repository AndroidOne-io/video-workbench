"""本地 HTTP Range 服务；.local/media.json 可按相同 URL 覆盖高清素材。"""
import argparse
import http.server
import io
import json
import re
import threading
import urllib.parse
import webbrowser
from pathlib import Path


def make_handler(root):
    root = Path(root).resolve()
    manifest = root / '.local/media.json'
    mapping = json.loads(manifest.read_text()) if manifest.is_file() else {}
    originals = {}
    for url, filename in mapping.items():
        p = Path(filename)
        p = p if p.is_absolute() else root / p
        if not p.is_file():
            raise FileNotFoundError(f'本地高清映射失效：{url} -> {p}')
        originals[url.lstrip('/')] = p.resolve()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self,*a,**kw):
            super().__init__(*a,directory=str(root),**kw)

        def log_message(self,*a):
            pass

        def translate_path(self,url):
            key = urllib.parse.unquote(urllib.parse.urlsplit(url).path).lstrip('/')
            self.original = key in originals
            return str(originals[key]) if self.original else super().translate_path(url)

        def end_headers(self):
            self.send_header('Accept-Ranges','bytes')
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Local-Media','original' if getattr(self,'original',False) else 'project')
            super().end_headers()

        def send_head(self):
            self.remaining = None
            key = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path).lstrip('/')
            # 本地私有目录不通过普通 URL 对外呈现；只能通过声明的素材 URL 读取。
            if any(part.startswith('.') for part in Path(key).parts):
                self.send_error(404); return None
            if key == '__local_hd_status__':
                data = json.dumps({'mode':'local-hd' if originals else 'project',
                                   'originals':list(originals)}).encode()
                self.send_response(200); self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(data)));self.end_headers()
                return io.BytesIO(data)
            p = Path(self.translate_path(self.path))
            rng = self.headers.get('Range')
            if not rng or not p.is_file():
                if 'If-Modified-Since' in self.headers: del self.headers['If-Modified-Since']
                return super().send_head()
            size = p.stat().st_size
            m = re.fullmatch(r'bytes=(\d*)-(\d*)',rng)
            if not m or not any(m.groups()):
                self.send_error(400,'Only one byte range is supported');return None
            a,b = m.groups()
            if a:
                a,b = int(a),min(int(b) if b else size-1,size-1)
            else:
                a,b = max(0,size-int(b)),size-1
            if a > b or a >= size:
                self.send_response(416);self.send_header('Content-Range',f'bytes */{size}')
                self.send_header('Content-Length','0');self.end_headers();return None
            f = p.open('rb');f.seek(a);self.remaining = b-a+1
            self.send_response(206);self.send_header('Content-Type',self.guess_type(str(p)))
            self.send_header('Content-Range',f'bytes {a}-{b}/{size}')
            self.send_header('Content-Length',str(self.remaining));self.end_headers()
            return f

        def copyfile(self,source,output):
            try:
                if self.remaining is None:return super().copyfile(source,output)
                while self.remaining:
                    chunk = source.read(min(self.remaining,1024*1024))
                    if not chunk:break
                    output.write(chunk);self.remaining -= len(chunk)
            except (BrokenPipeError,ConnectionResetError):
                pass

    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--port',type=int,default=8771)
    ap.add_argument('--no-open',action='store_true')
    args = ap.parse_args()
    if not (args.root/'index.html').is_file():ap.error('root 下没有 index.html')
    server = http.server.ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(args.root))
    url=f'http://127.0.0.1:{server.server_port}/index.html'
    print(url,flush=True)
    if not args.no_open:threading.Timer(.3,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__ == '__main__':main()
