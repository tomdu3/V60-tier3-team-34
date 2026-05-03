import sys
import os
from pathlib import Path

# Add the server directory to sys.path so relative imports work
server_dir = str(Path(__file__).parent.parent / "server")
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from server.main import app
