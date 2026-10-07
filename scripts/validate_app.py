"""Exercise every page against existing curated data; never reads raw CSVs."""
from pathlib import Path
import json
import os
from streamlit.testing.v1 import AppTest

if __name__ == '__main__':
    os.environ.setdefault('OLIST_DATA_ROOT', 'data')
    os.environ['OLIST_BACKEND'] = 'local'
    app = AppTest.from_file('app/app.py', default_timeout=90).run()
    if app.exception or app.error:
        raise RuntimeError(f'Landing page failed: {app.exception} {app.error}')
    outcomes = []
    for page in app.sidebar.radio[0].options:
        app.sidebar.radio[0].set_value(page).run()
        if app.exception or app.error:
            raise RuntimeError(f'{page} failed: {app.exception} {app.error}')
        outcomes.append({'page': page, 'status': 'PASSED'})
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/app_smoke.json').write_text(json.dumps(outcomes, indent=2))
    print(json.dumps(outcomes, indent=2))
