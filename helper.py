import json
import subprocess

stl_log_filename = '.stl.log'

def parse_json(json_file):
    with open(json_file, 'r') as f:
        s = f.read()
        obj = json.loads(s)

    l = obj['children'][0]['params']['length']
    w = obj['children'][0]['params']['width']
    h = obj['children'][0]['params']['height']
    n = obj['children'][0]['children'][0]['children'][0]['params']['noseLength']
    r = obj['children'][0]['children'][1]['children'][0]['children'][0]['params']['radius']
    t = obj['children'][0]['children'][2]['children'][0]['params']['tailLength']
    e = obj['children'][0]['children'][2]['children'][0]['params']['endRadius']
    
    return [l, w, h, n, r, t, e]

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

    # stl_filename = f'{stl_dir}/boxfish_{length}_{width}_{height}_{noseLength}_{radius}_{tailLength}_{endRadius}.stl'
    stl_filename = 'tmp.stl'
    json_str = json.dumps(data, separators=(',',':'))
    stl_cmd = f"npx jscad jscad-generator.js -o {stl_filename} --jsonComponentModel {json_str}"
    # print(f'Execute command: {stl_cmd}')
    with open(stl_log_filename, 'w') as outfile:
        subprocess.run(stl_cmd.split(' '), stdout=outfile, stderr=outfile)
    return stl_filename
