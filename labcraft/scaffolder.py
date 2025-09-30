from pathlib import Path
import datetime
import json

DEFAULTS = ['notes', 'enum', 'scans', 'scripts', 'loot', 'reports', 'extra']
META = 'labcraft.json'

def init_project(root: Path, template=None, force=False):
    """Inicializa un proyecto
    Devuelve True si se creó, False si ya existía y no se usó --force.
    Con el parámetro --force se reescribe el directorio. 
    """
    root = root.expanduser().resolve()
    meta_file = root / META

    if meta_file.exists() and not force:
        return False
    
    for d in DEFAULTS:
        (root / d).mkdir(parents=True, exist_ok=True)

    meta = {
        'name': root.name,
        'created': datetime.datetime.now().isoformat() + 'Z', 
        'template': template
    }
    
    meta_file.write_text(json.dumps(meta, indent=2))

    return True