"""Execute collection scripts through Django's test client without network access."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

def main():
    """Run the Postman collection against a temporary database via Django's test client.

    A Node.js helper evaluates the collection's JavaScript assertions and asks this
    process to perform each HTTP request in-process. A summary of the run is written
    to ``postman/test-results.json``.

    Returns:
        The exit code of the Node.js runner (0 if all assertions passed).
    """
    import django
    from django.conf import settings
    with tempfile.TemporaryDirectory(prefix='coderr-postman-', dir=ROOT) as temp:
        settings.DATABASES['default']['NAME'] = str(Path(temp) / 'test.sqlite3')
        settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
        django.setup()
        from django.core.management import call_command
        from django.db import connections
        from django.test import Client
        from urllib.parse import urlsplit
        try:
            call_command('migrate', verbosity=0, interactive=False)
            client = Client()
            report_path = Path(temp) / 'report.json'
            command = [shutil.which('node') or 'node', str(ROOT / 'postman/run_collection.cjs'),
                       str(ROOT / 'postman/Coderr.postman_collection.json'),
                       'http://127.0.0.1:8000', str(report_path)]
            process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, text=True, encoding='utf-8')
            for line in process.stdout:
                if not line.startswith('REQUEST '):
                    print(line, end='')
                    continue
                request = json.loads(line[len('REQUEST '):])
                url = urlsplit(request['url'])
                path = url.path + ('?' + url.query if url.query else '')
                headers = {key: value for key, value in request['headers'].items()
                           if key.lower() != 'content-type'}
                response = client.generic(request['method'], path,
                    data=request.get('body') or '', content_type='application/json', headers=headers)
                process.stdin.write(json.dumps({'status': response.status_code,
                                                'body': response.content.decode('utf-8')}) + '\n')
                process.stdin.flush()
            result = process.wait()
            process.stdin.close()
            process.stdout.close()
            if report_path.exists():
                report = json.loads(report_path.read_text(encoding='utf-8'))
                summary = {'runner': 'Django test client + local JavaScript assertions (not Postman/Newman)',
                           'stats': report['run']['stats'],
                           'failures': [{'name': f.get('source', {}).get('name'),
                                         'message': f.get('error', {}).get('message')}
                                        for f in report['run']['failures']]}
                (ROOT / 'postman/test-results.json').write_text(
                    json.dumps(summary, indent=2), encoding='utf-8')
            return result
        finally:
            connections.close_all()

if __name__ == '__main__':
    raise SystemExit(main())
