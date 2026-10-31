from pathlib import Path
import importlib.util,re,sys,tempfile,threading,unittest,urllib.request
from board import project
from board.app import create_server

ROOT=Path(__file__).resolve().parents[1]

class LanguageDelivery(unittest.TestCase):
    def test_readme_images_are_in_source_release(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location('language_release',ROOT/'scripts/release.py')
        release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
        shipped=set(release.files())
        self.assertTrue(all((ROOT/name).is_file() for name in shipped))
        for name in ['README.md','README.zh-CN.md']:
            text=(ROOT/name).read_text('utf-8')
            images=re.findall(r'<img[^>]+src="([^"]+)"|!\[[^\]]*\]\(([^)]+)\)',text)
            for alternatives in images:
                image=next(x for x in alternatives if x)
                if not image.startswith('http'):self.assertIn(image,shipped)

    def test_english_assets_are_served_by_real_local_listener(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root=Path(tmp.name);project.initialize(root,'Language test','Compare','Report')
        server=create_server(root,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for name,marker in [('i18n.js',b'BoardI18n'),('i18n.css',b'language-control'),('help.en.html',b'lang="en"')]:
                with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/{name}',timeout=5) as response:
                    self.assertEqual(response.status,200);self.assertIn(marker,response.read())
        finally:server.shutdown();thread.join();server.server_close()

if __name__=='__main__':unittest.main()
