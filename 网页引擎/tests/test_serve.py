"""标准库测试：断点请求和本地高清覆盖不能悄悄退回便携文件。"""
import http.server
import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('preview_serve',Path(__file__).resolve().parents[1]/'serve.py')
MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)


class MediaServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'clip.mp4').write_bytes(b'portable')
        (self.root/'.local').mkdir()
        (self.root/'.local/original.mp4').write_bytes(b'0123456789abcdef')
        (self.root/'.local/media.json').write_text(json.dumps({'clip.mp4':'.local/original.mp4'}))
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),MODULE.make_handler(self.root))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}/'

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()

    def request(self,path='clip.mp4',rng=None):
        return urllib.request.urlopen(urllib.request.Request(self.base+path,headers={'Range':rng} if rng else {}))

    def test_original_and_ranges(self):
        with self.request() as r:
            self.assertEqual(r.status,200);self.assertEqual(r.headers['X-Local-Media'],'original')
            self.assertEqual(r.read(),b'0123456789abcdef')
        for rng,want in [('bytes=2-5',b'2345'),('bytes=-4',b'cdef'),('bytes=12-',b'cdef')]:
            with self.request(rng=rng) as r:
                self.assertEqual(r.status,206);self.assertEqual(r.read(),want)
                self.assertEqual(int(r.headers['Content-Length']),len(want))

    def test_bad_range_and_private_directory(self):
        for path,rng,code in [('clip.mp4','bytes=99-',416),('clip.mp4','bytes=1-2,4-5',400),
                              ('.local/media.json',None,404)]:
            with self.assertRaises(urllib.error.HTTPError) as cm:self.request(path,rng)
            self.assertEqual(cm.exception.code,code)
            cm.exception.close()

    def test_missing_original_is_error(self):
        (self.root/'.local/original.mp4').unlink()
        with self.assertRaises(FileNotFoundError):MODULE.make_handler(self.root)


if __name__=='__main__':unittest.main()
