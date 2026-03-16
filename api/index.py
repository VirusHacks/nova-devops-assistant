import sys
import os
from pathlib import Path

# Add the project root to sys.path so we can import github_app
sys.path.append(str(Path(__file__).parent.parent))

from github_app.webhook_server import app
