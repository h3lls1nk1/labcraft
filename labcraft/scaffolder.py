from pathlib import Path
import datetime
import json
from jinja2 import Environment
from .templates import discover_template, load_manifest, apply_template, read_template_bytes

META = 'labcraft.json'
ENV = Environment(autoescape=False)

def init_project(root: Path, template=None, force=False, template_vars=None):
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
        ctx = {**defaults, **(template_vars or {})}
        ctx.update({
            'project_name': root.name,
            'created': datetime.datetime.now().isoformat() + 'Z',
        })
        
        files = manifest.get('files')
        if files:
            for item in files:
                if item.endswith('/'):  # directorio
                    (root / item).mkdir(parents=True, exist_ok=True)
                    continue
                
                # Calcular ruta de destino
                if item.endswith('.j2'):
                    # Eliminar .j2 del nombre
                    dest_name = item[:-3]  # Quita los últimos 3 caracteres (.j2)
                else:
                    dest_name = item
                
                dest = root / dest_name
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    # read_template_bytes puede devolver una tupla o bytes
                    result = read_template_bytes(tpl, item)
                    
                    # Si es una tupla, tomar el primer elemento
                    if isinstance(result, tuple):
                        src_bytes = result[0]
                    else:
                        src_bytes = result
                    
                    if item.endswith('.j2'):
                        # Es una plantilla Jinja2, renderizarla
                        text = src_bytes.decode('utf-8')
                        tmpl = ENV.from_string(text)
                        rendered = tmpl.render(**ctx)
                        dest.write_text(rendered, encoding='utf-8')
                    else:
                        # Archivo normal, copiar tal cual
                        dest.write_bytes(src_bytes)
                        
                except FileNotFoundError:
                    print(f"Advertencia: No se encontró el archivo de plantilla '{item}'")
                except Exception as e:
                    print(f"Error procesando '{item}': {e}")
                    raise
        else:
            apply_template(tpl, root, ctx)
    else:
        for d in ['notes','enum','scans','scripts','loot','reports','extra']:
            (root / d).mkdir(parents=True, exist_ok=True)
    
    meta = {
        'name': root.name,
        'created': datetime.datetime.now().isoformat() + 'Z',
        'template': template
    }
    meta_file.write_text(json.dumps(meta, indent=2))
    return True