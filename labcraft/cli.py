import click
from pathlib import Path
from labcraft import scaffolder

@click.group()
def cli():
    """CLI principal de labcraft"""
    pass

@cli.command()
@click.argument('path', required=False, default='.')
@click.option('--template', default=None, help='Plantilla de proyecto')
@click.option('--force', is_flag=True, help='Sobreescribe si ya existe')
def init(path, template, force):
    """Inicializa estructura básica de laboratorio"""
    root = Path(path)

    created = scaffolder.init_project(root, template, force)

    if created:
        click.echo(f'Proyecto creado en {root.resolve()}')
    else:
        click.echo(f'Ya existe un proyecto en {root.resolve()}. Usa --force para sobreescribir')
