import random
import os
import subprocess

import chevron
from slugify import slugify
from loguru import logger

YARLE_VERSION = "4.8"
YARLE_CONFIG_TEMPLATE = os.path.join(os.path.dirname(__file__), "yarle_config.json.tmpl")
YARLE_TEMPLATE = os.path.join(os.path.dirname(__file__), "yarle_format.tmpl")


def enex2md(enexfile=None, outdir=None, md_format_type="StandardMD", yarle_config=None, yarle_template=YARLE_TEMPLATE,
            item=None):
    """Make a dict out of the parsed, supplied lines"""

    cfgint = random.randint(1, 9999999999)
    #    cfgfile = os.path.join(OUTPUT_DIR, f'configs/config{cfgint}.json')
    basefile = os.path.basename(item['input_file'])
    basefilepts = basefile.split(".")
    if len(basefilepts) > 1:
        basefile = "".join(basefilepts[:-1])

    if not yarle_config:
        yarle_config = os.path.join(outdir, f'{basefile}.json')

    process = None
    try:
        with open(YARLE_CONFIG_TEMPLATE, 'r') as f:
            jsonfile = chevron.render(f, item)

        with open(yarle_config, "w") as jfp:
            jfp.write(jsonfile)

        cmd = f'npx -p yarle-evernote-to-md@{YARLE_VERSION} yarle --configFile "{yarle_config}"'

        item = item | {
            "output_dir": outdir | os.path.dirname(enexfile),
            "template_file": yarle_template,
            "resources_subdir": "." + slugify(basefile) + "_resources",
            "yarle_config_file": yarle_config,
            "stack_dir": None,
            "notebook_dir": None,
            "md_format_type": md_format_type
        }

        logger.debug(f'\t\t... calling: {cmd}')
        process = subprocess.run(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True,
                                 shell=True, check=False)
        process.check_returncode()

        item['process_result'] = "success"
        return item

    except Exception as e:
        logger.error(f'Failed to convert {item["input_file"]} due to error:  {process.stderr}')
        item['process_result'] = str(process.stderr)
        pass

    return item
