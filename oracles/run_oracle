#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
import subprocess

use_cfd = True

stl_dir = 'stl'
Path(stl_dir).mkdir(parents=True, exist_ok=True)
stl_log_filename = '.stl.log'
cfd_log_filename = '.cfd.log'

def gen_stl(length, width, height, noseLength, radius, tailLength, endRadius):
    # Generate boxfish stl file
    data = {
            "type": "root",
            "params": {"segments":128},
            "children": [
                {
                    "type": "SingleHull",
                    "params": {
                        "length": length, #2400,
                        "width": width, #700,
                        "height": height, #700
                        },
                    "children": [
                        {
                            "type": "Front",
                            "children": [
                                {
                                    "type": "LinearNoseCone",
                                    "params": {
                                        "noseLength": noseLength, #15
                                        }
                                    }
                                ]
                            },
                        {
                            "type": "Midsection",
                            "children": [
                                {
                                    "type": "Midshape",
                                    "children": [
                                        {
                                            "type": "Boxfish",
                                            "params": 
                                            {
                                                "rounded": 1,
                                                "radius": radius, #200
                                                }
                                            }
                                        ]
                                    }
                                ]
                            },
                        {
                            "type": "Tail",
                            "children": [
                                {
                                    "type": "LinearTailCone",
                                    "params": {
                                        "tailLength": tailLength, #15,
                                        "endRadius": endRadius, #100
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }

    stl_filename = f'{stl_dir}/boxfish_{length}_{width}_{height}_{noseLength}_{radius}_{tailLength}_{endRadius}.stl'
    json_str = json.dumps(data, separators=(',',':'))
    stl_cmd = f"npx jscad jscad-generator.js -o {stl_filename} --jsonComponentModel {json_str}"
    # print(f'Execute command: {stl_cmd}')
    with open(stl_log_filename, 'w') as outfile:
        subprocess.run(stl_cmd.split(' '), stdout=outfile, stderr=outfile)
    return stl_filename

def run_cfd_sim(stl_filename, aoa=0):
    exe = "/Users/pwchen/code/LOGiCS/test_dexof/test_casestudy/run_dexof.sh"
    cfd_cmd = f"{exe} rough_mesh_8cores.dex {stl_filename} {aoa}"
    # print(f'Execute command: {cfd_cmd}')
    with open(cfd_log_filename, 'w') as outfile:
        subprocess.run(cfd_cmd.split(' '), stdout=outfile, stderr=outfile)

def run_surrogate(stl_filename):
    exe = f"/Users/pwchen/code/LOGiCS/CFD_ML/run_surrogate.sh"
    stl_filename = os.path.abspath(stl_filename)
    sur_cmd = f"{exe} {stl_filename}"
    with open(cfd_log_filename, 'w') as outfile:
        subprocess.run(sur_cmd.split(' '), stdout=outfile, stderr=outfile)

def parse_drag():
    if use_cfd:
        grep_cmd = f"grep Cd {cfd_log_filename}"
        s = subprocess.check_output(grep_cmd.split(' ')).decode("utf-8")
        s = s.split()
        i = len(s) - 1 - s[::-1].index('Cd') # Find the last Cd
        assert i+2 < len(s)
        drag = float(s[i+2]) # [..., 'Cd', ':', 'x.xxx', ...]
    else:
        with open(cfd_log_filename, 'r') as f:
            drag = eval(f.readlines()[0])
    return drag

def parse_volume():
    with open(stl_log_filename, 'r') as f:
        line = f.readlines()[-1]
        return json.loads(line)['volume']


if __name__ == '__main__':
    run_cfd = sys.argv[1] == 'cfd'
    run_vol = sys.argv[1] == 'vol'
    assert run_cfd or run_vol

    args = [int(arg) for arg in sys.argv[2:]]

    length = args[0]
    width = args[1]
    height = args[2]
    noseLength = args[3]
    radius = args[4]
    tailLength = args[5]
    endRadius = args[6]

    stl_filename = gen_stl(length, width, height, noseLength, radius, tailLength, endRadius)
    if run_cfd:
        if use_cfd: run_cfd_sim(stl_filename)
        else: run_surrogate(stl_filename)
        drag = parse_drag()
        dragx1000 = int(drag * 1000)
        print(dragx1000)
    if run_vol:
        volume = parse_volume()
        print(int(volume))
