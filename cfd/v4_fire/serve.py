"""Serve local V4 CFD viewer and imported preriscaldamento outputs."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import mimetypes

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'v4_fire/web'
RUN=ROOT/'home_pc/campaign/preheat'
BAKE=ROOT/'home_pc/campaign/bake'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        route=unquote(urlsplit(self.path).path)
        if route in ('/','/v4-fire','/v4-fire/'):
            base=WEB;relative='index.html'
        elif route.startswith('/v4-fire/preheat-data/'):
            base=RUN/'visualisation';relative=route[len('/v4-fire/preheat-data/'):]
        elif route.startswith('/v4-fire/preheat-video/'):
            base=RUN/'video';relative=route[len('/v4-fire/preheat-video/'):]
        elif route.startswith('/v4-fire/bake-data/'):
            base=BAKE/'visualisation';relative=route[len('/v4-fire/bake-data/'):]
        elif route.startswith('/v4-fire/bake-video/'):
            base=BAKE/'video';relative=route[len('/v4-fire/bake-video/'):]
        elif route.startswith('/v4-fire/'):
            base=WEB;relative=route[len('/v4-fire/'):]
        else:
            self.send_error(404);return
        base=base.resolve();target=(base/relative).resolve()
        if not target.is_relative_to(base) or not target.is_file():
            self.send_error(404);return
        mime='text/javascript' if target.suffix=='.js' else mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        self.send_response(200)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(target.stat().st_size))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        with target.open('rb') as f:
            while data:=f.read(1024*1024):self.wfile.write(data)

if __name__=='__main__':
    print('http://127.0.0.1:8766/v4-fire/?model=preheat',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8766),Handler).serve_forever()
