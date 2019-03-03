#!/usr/bin/env python
#
# Create project files for all BTstack embedded examples in WICED/apps/btstack

import os
import re
import shutil
import subprocess
import sys


gatt_update_template = '''#!/usr/bin/env python

import subprocess
import os
import sys

# get project path
project_path = os.path.abspath(os.path.dirname(sys.argv[0])) + '/'

print('Creating EXAMPLE.h from EXAMPLE.gatt')

# execute script
compile_gatt_script = project_path + "/btstack/tool/compile_gatt.py"
gatt_file = project_path + '/example/EXAMPLE.gatt'
h_file    = project_path + '/example/EXAMPLE.h'
print(gatt_file)
print(h_file)
subprocess.call([compile_gatt_script, gatt_file, h_file])
'''


## pick correct init script based on your hardware
# - init script for CC2564B
cc256x_init_script = 'bluetooth_init_cc2564B_1.6_BT_Spec_4.1.c'
# - init script for CC2564C
# cc256x_init_script = 'bluetooth_init_cc2564C_1.0.c'


# fetch init script
print("Creating init script %s" % cc256x_init_script)
subprocess.call("make " + cc256x_init_script, shell=True)

# get script path
script_path = os.path.abspath(os.path.dirname(sys.argv[0])) + '/'

# get btstack root
btstack_root = script_path + '../../'

# path to examples
examples_embedded = btstack_root + "example/"

# path to generated example projects
projects_path = script_path + "example/"

# path to eclipse template
eclipse_template = script_path + 'eclipse-template/'

print("Creating Eclipse example projects in example:")

# iterate over btstack examples
example_files = os.listdir(examples_embedded)

# single example
# example_files = ['spp_and_le_counter.c']

for file in example_files:
    if not file.endswith(".c"):
        continue
    example = file[:-2]

    # create folder
    project_folder = projects_path + example + "/"
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)

    # copy folder from template
    for folder in ['.settings', 'include', 'ldscripts', 'src', 'system']:
        src_folder  = eclipse_template + folder
        dest_folder = project_folder + folder
        if os.path.exists(dest_folder):
            shutil.rmtree(dest_folder)
        shutil.copytree(src_folder, dest_folder)

    # create customized example folder
    example_folder = project_folder + 'example/'
    if not os.path.exists(example_folder):
        os.makedirs(example_folder)
    shutil.copy(examples_embedded + file, example_folder)

    # add CC2564B init script
    shutil.copy(script_path + cc256x_init_script, example_folder)

    # add sco_demo_util.c for audio examples
    if example in ['hfp_ag_demo','hfp_hf_demo', 'hsp_ag_demo', 'hsp_hf_demo']:
        shutil.copy(examples_embedded + 'sco_demo_util.c', example_folder)
        shutil.copy(examples_embedded + 'sco_demo_util.h', example_folder)

    # copy .cproject
    shutil.copy(eclipse_template+'.cproject', project_folder)

    # copy debug configuration and update project name
    with open(project_folder + example + '-debug.launch', "wt") as fout:
        with open(eclipse_template + 'stm32f4discovery-template-debug.launch', "rt") as fin:
            for line in fin:
                fout.write(line.replace('stm32f4discovery-template', example))

    # copy project files and update project name
    with open(project_folder + '.project', "wt") as fout:
        with open(eclipse_template + '.project', "rt") as fin:
            for line in fin:
                fout.write(line.replace('stm32f4discovery-template', example))

    # copy btstack subset
    btstack_tree = project_folder + 'btstack/'
    if os.path.exists(btstack_tree):
        shutil.rmtree(btstack_tree)
    for subtree in ['3rd-party/bluedroid', '3rd-party/hxcmod-player', '3rd-party/micro-ecc', '3rd-party/md5', '3rd-party/segger-rtt', '3rd-party/yxml', 'chipset/cc256x', 'platform/embedded', 'port/stm32-f4discovery-cc256x/src', 'port/stm32-f4discovery-cc256x/pdm', 'src']:
        shutil.copytree(btstack_root + subtree, btstack_tree + subtree)

    # create update_gatt.sh if .gatt file is present
    gatt_path = examples_embedded + example + ".gatt"
    if os.path.exists(gatt_path):
        # copy .gatt file
        shutil.copy(gatt_path, example_folder)
        # install compile_gatt.py
        tool_path = btstack_tree + 'tool/'
        os.makedirs(tool_path)
        compile_gatt_path = tool_path + 'compile_gatt.py'
        shutil.copy(btstack_root + 'tool/compile_gatt.py', compile_gatt_path)
        os.chmod(compile_gatt_path, 0o755)
        # create example/update_gatt_db.sh
        update_gatt_script = project_folder + "update_gatt_db.py"
        with open(update_gatt_script, "wt") as fout:
            fout.write(gatt_update_template.replace("EXAMPLE", example))        
        os.chmod(update_gatt_script, 0o755)
        # execute script
        subprocess.call(update_gatt_script + "> /dev/null", shell=True)
        print("- %s including compiled GATT DB" % example)
    else:
        print("- %s" % example)

print("Projects are ready for import into Eclipse CDT. See README for details.")
