import os
import shutil
import json
from pathlib import Path
import yaml
import datetime
from importlib import resources
from jinja2 import Template, Environment, meta
from typing import Tuple

XDG_CONFIG_HOME = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
USER_TEMPLATES_DIR = XDG_CONFIG_HOME / 'labcraft' / 'templates'

BUILTIN_TEMPLATES_PACKAGE = 'labcraft.data.templates'

def ensure_user_templates_dir():
    USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

def list_builtin_templates():
    """Listar nombres de templates embebidas.
    """
    templates = []

    try:
        root = resources.files(BUILTIN_TEMPLATES_PACKAGE)

        for t in root.iterdir():
            if t.is_dir():
                templates.append(t.name)
    except Exception:
        pass

    return templates

def list_user_templates():
    ensure_user_templates_dir()

    return [p.name for p in USER_TEMPLATES_DIR.iterdir() if p.is_dir()]

def discover_template(name):
    """Devuelve Path a la plantilla (prioridad: project-local -> user -> builtin)
    """
    proj_local = Path.cwd() / 'templates' / name

    if proj_local.exists():
        return proj_local
    
    user_path = USER_TEMPLATES_DIR / name

    if user_path.exists():
        return user_path
    
    try:
        root = resources.files(BUILTIN_TEMPLATES_PACKAGE) / name

        if root.exists():
            return root
    except Exception:
        pass

    return None

def load_manifest(template_path):
    """
    template_path: Path or importlib.resources Traversable
    Returns dict (may be empty)
    """
    try:
        if hasattr(template_path, 'read_text'):
            manifest = template_path / 'template.yml'

            if manifest.exists():
                return yaml.safe_load(manifest.read_text()) or {}
            
            manifest_json = template_path / 'template.json'

            if manifest_json.exists():
                return json.loads(manifest_json.read_text()) or {}
            
            return {}
    except Exception:
        pass

    try:
        manifest_file = template_path.joinpath('template.yml')

        if manifest_file.exists():
            return yaml.safe_load(manifest_file.read_text()) or {}
    except Exception:
        pass

    return {}

def _is_binary_string(b: bytes) -> bool:
    if b'\x00' in b:
        return True
    
    try:
        b.decode('utf-8')
        
        return False
    except Exception:
        return True
    
def apply_template(template_source, dest: Path, context: dict):
    """
    template_source: Path or importlib.resources Traversable
    dest: Path to create
    context: dict with variables for jinja
    """
    env = Environment()

    dest.mkdir(parents=True, exist_ok=True)

    try:
        items = list(template_source.iterdir()) 
        is_traversable = True
    except Exception:
        items = list(Path(template_source).rglob('*'))
        is_traversable = False

    if is_traversable:
        def walk(trav, rel=''):
            for ch in trav.iterdir():
                cur_rel = (Path(rel) / ch.name)

                if ch.is_dir():
                    (dest / cur_rel).mkdir(parents=True, exist_ok=True)
                    walk(ch, str(cur_rel))
                else:
                    # file
                    write_template_file(ch.read_bytes(), dest / cur_rel, context, env)
        walk(template_source)
    else:
        # using pathlib Path rglob gives full paths; skip directories themselves handled by parents
        for src in items:
            rel = src.relative_to(template_source)
            target = dest / rel
            if src.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            data = src.read_bytes()
            write_template_file(data, target, context, env)

def write_template_file(raw_bytes: bytes, target: Path, context: dict, env: Environment):
    # if filename endswith .j2 -> render as text with jinja (and strip .j2)
    if target.name.endswith('.j2'):
        target = target.with_suffix('')  # remove .j2
        text = raw_bytes.decode('utf-8')
        tmpl = env.from_string(text)
        rendered = tmpl.render(**context)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding='utf-8')
    else:
        # if looks like binary -> copy as binary
        if _is_binary_string(raw_bytes):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw_bytes)
        else:
            # treat as text, but do NOT render unless user requested; keep exact content
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(raw_bytes.decode('utf-8'), encoding='utf-8')

def read_template_bytes(template_source, rel_path: str) -> Tuple[bytes, bool]:
    """
    Lee y devuelve el contenido (bytes) del archivo rel_path dentro de template_source.
    Devuelve (bytes, is_traversable) donde is_traversable indica si el source era Traversable.
    Lance FileNotFoundError si no existe.
    template_source puede ser:
      - importlib.resources.Traversable  (has .joinpath(), .read_bytes())
      - pathlib.Path
    rel_path usa '/' como separador (ej: 'notes/info.md.j2').
    """
    # 1) Si template_source parece Traversable (importlib.resources)
    try:
        # many Traversable implementations have joinpath() or joinpath-like behaviour
        candidate = template_source.joinpath(rel_path)
        # read_bytes en Traversable
        data = candidate.read_bytes()
        return data, True
    except Exception:
        pass

    # 2) fallback Path
    candidate_path = Path(template_source) / rel_path
    if candidate_path.exists():
        return candidate_path.read_bytes(), False

    # 3) si no existe
    raise FileNotFoundError(f"Plantilla no contiene el archivo: {rel_path}")

def read_template_text(template_source, rel_path: str, encoding='utf-8') -> Tuple[str, bool]:
    b, trav = read_template_bytes(template_source, rel_path)
    return b.decode(encoding), trav