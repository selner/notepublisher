import logging

from notepublisher import exportnotebook
from notepublisher.helpers.configs import load_config_from_json
from notepublisher.helpers.dicts import merge
import click

from loguru import logger

logger.level("DEBUG")


@click.command(context_settings=dict(
    allow_extra_args = True,
    allow_interspersed_args = True,
    ignore_unknown_options=True
))
@click.argument('config', nargs=1, type=str)
@click.argument('output_path', nargs=1, type=str)

# @click.argument("-c", "--config", help="Configuration file", default="./notepublisher.cfg ", show_default=True,
#               type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True))
# @click.option("-o", "--output", help="Output directory", default="./, ", show_default=True,
#               type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, resolve_path=True))
@click.option("-s", "--formats", help="Note export formats", multiple=True, default=['html'], show_default=True)
@click.option("-s", "--stack", help="Match notebooks in stacks with names matching this string", default=None,
              show_default=False)
@click.option("-s", "--notebook", help="Match notebooks with names matching this string", default=None,
              show_default=False)
@click.option('/debug;/no-debug')
@click.version_option()
def cli(config, output_path, formats, stack, notebook, debug):
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)

    params = {
        "config": config,
        "output_path": output_path,
        "formats": formats,
        "stack": stack,
        "notebook": notebook,
        "debug": debug
    }

    logger.info(f'Export called.  Context: {params}')
    appctx = params
    if "config" in appctx:
        json_config = load_config_from_json(appctx['config'])
        appctx = merge(json_config, appctx)

        # Arguments take priority over JSON:

    exportobj = exportnotebook.NotebooksExport(appctx)
    exportobj.export_search()

    if __name__ == '__main__':
        cli(obj={})


#
# #
# cli_usage = """
# Usage:
#   notepublisher.py [-c FILE] [-o DIR] [--matchstack=STRING] [--matchnotebook=STRING] [--formats=PATTERNS]
#   notepublisher.py --version
#
# Options:
#   -h --help  show this help message and exit
#   --version  show version and exit
#   -v --verbose  print status messages
#   -o DIR --output=DIR  output directory [default: ./]
#   -c FILE --config=FILE  config settings directory [default: ./notepublisher.cfg]
#   --matchstack=STRING  string to match stack names against when searching
#   --matchnotebook=STRING  string to match notebook names against when searching
#   --formats=PATTERNS   export notes to file formats which match these comma
#                        separated patterns [default: html,enex]
# """

# from docopt import docopt


if __name__ == '__main__':
    cli()
