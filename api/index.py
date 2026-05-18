import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "converter"))

from converter.web.app import create_app

app = create_app(max_upload_mb=4)
