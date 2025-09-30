from pathlib import Path
import datetime
import json
from .templates import discover_template, load_manifest, apply_template

META = 'labcraft.json'

def init_project(root: Path, template=None, force=False, vars=None):
    """Inicializa un proyecto
    Devuelve True si se creó, False si ya existía y no se usó --force.
    Con el parámetro --force se reescribe el directorio. 
    """
    root = root.expanduser().resolve()
    meta_file = root / META

    if meta_file.exists() and not force:
        return False
    
    root.mkdir(parents=True, exist_ok=True)

    if template:
        tpl = discover_template(template)

        if tpl is None:
            raise FileNotFoundError(f'Template {template} no encontrada')
        
        manifest = load_manifest(tpl)
        defaults = manifest.get('variables', {})
        ctx = {**defaults, **(vars or {})}
        ctx.update({
            'project_name': root.name,
            'created': datetime.datetime.now().isoformat() + 'Z',
        })
        
        apply_template(tpl, root, ctx)
    else:
        for d in ['notes','enum','scans','scripts','loot','reports','extra']:
            (root / d).mkdir(parents=True, exist_ok=True)

    meta = {'name': root.name, 'created': datetime.datetime.now().isoformat() + 'Z', 'template': template}
    meta_file.write_text(json.dumps(meta, indent=2))

    return True