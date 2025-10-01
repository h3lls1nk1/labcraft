import click
from pathlib import Path
from labcraft import scaffolder

def parse_vars(ctx, param, value):
    d = {}

    if not value:
        return d
    
    for item in value:
        if '=' not in item:
            raise click.BadParameter('Variables deben ser KEY=VAL')
        
        k, v = item.split('=', 1)

        d[k.strip()] = v.strip()

        return d

@click.group()
def cli():
    """CLI principal de labcraft"""
    pass

@cli.command()
@click.argument('path', required=False, default='.')
@click.option('--template', '-t', default=None, help='Plantilla de proyecto')
@click.option('--var', multiple=True, callback=parse_vars, help='Variables para la plantilla, formato KEY=VALUE')
@click.option('--force', is_flag=True, help='Sobreescribe si ya existe')
def init(path, template, var, force):
    """Inicializa estructura básica de laboratorio"""
    root = Path(path)

    ok = scaffolder.init_project(
        root=root, 
        template=template, 
        force=force, 
        template_vars=var
    )

    if ok:
        click.echo('Proyeto creado')
    else:
        click.echo('Ya existe un proyecto con ese nombre (usa --force para sobreescribir)')
