"""Configuration des tests RustSensei.

Ajoute les chemins nécessaires aux imports des modules du projet
(app/ et scripts/) pour les tests.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

for _path in (PROJECT_ROOT, SCRIPTS_DIR):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)
