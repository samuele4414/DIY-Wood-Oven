"""Local CFD viewer: rebuild on page requests, using actual run outputs."""
import argparse
import importlib.util
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import mimetypes
from urllib.parse import unquote

from collect_results import collect
from run_study import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--family', default='coarse_dx40_t30')
    parser.add_argument('--renderer', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('viewer_renderer', args.renderer)
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    lock = threading.Lock()
    cache = {'time': 0, 'page': None}
    preview = ROOT/'preview'
    preview.mkdir(exist_ok=True)

    def page():
        with lock:
            if cache['page'] is None or time.monotonic()-cache['time'] > 15:
                fragment_path = preview/'current-fragment.html'
                collect(args.family, fragment_path)
                html = renderer._render_document(fragment_path.read_text(encoding='utf-8'), 'Forno — CFD')
                html = html.replace('<head>', '<head><meta http-equiv="refresh" content="60">', 1)
                html = html.replace('<body>', '<body><a href="/v4-fire/" style="display:block;padding:16px;background:#18232d;color:#ffd18a;font:18px system-ui">Apri V4: fiamma e fumo in 3D</a>', 1)
                cache['page'] = html.encode('utf-8')
                cache['time'] = time.monotonic()
                (preview/'index.html').write_bytes(cache['page'])
            return cache['page']

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = unquote(self.path.split('?')[0])
            if route.startswith('/v4-fire/'):
                web = (ROOT/'v4_fire'/'web').resolve()
                asset = (web/(route[len('/v4-fire/'):] or 'index.html')).resolve()
                if not asset.is_relative_to(web) or not asset.is_file():
                    self.send_error(404)
                    return
                body = asset.read_bytes()
                self.send_response(200)
                mime = 'text/javascript' if asset.suffix == '.js' else mimetypes.guess_type(str(asset))[0] or 'application/octet-stream'
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path.split('?')[0] not in ('/', '/index.html'):
                self.send_error(404)
                return
            try:
                body = page()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as error:
                print(f'Viewer build failed: {error}', flush=True)
                self.send_error(500, 'Impossibile aggiornare i risultati; consultare viewer_error.log')

    page()
    print(f'http://127.0.0.1:{args.port}/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
