import json
import os
import pandas as pd

def get_name(i):
    return f'uuv_{str(i).zfill(4)}'

n = 500

names = []
ls, ws, hs, ns, rs, ts, es, dfs, cds, ras = [], [], [], [], [], [], [], [], [], []

for i in range(n):
    filename = get_name(i)
    names.append(filename)
    with open(os.path.join('json', filename+'.json'), 'r') as f:
        line = f.readlines()[0].strip()
        j = json.loads(line)
        ls.append(j['children'][0]['params']['length'])
        ws.append(j['children'][0]['params']['width'])
        hs.append(j['children'][0]['params']['height'])
        ns.append(j['children'][0]['children'][0]['children'][0]['params']['noseLength'])
        rs.append(j['children'][0]['children'][1]['children'][0]['children'][0]['params']['radius'])
        ts.append(j['children'][0]['children'][2]['children'][0]['params']['tailLength'])
        es.append(j['children'][0]['children'][2]['children'][0]['params']['endRadius'])
    df = os.popen(f"grep Total results/{filename}.log" + " | head -n 1 | awk '{print $3}'").read().strip()[1:]
    cd = os.popen(f"grep Cd results/{filename}.log" + " | awk '{print $3}'").read().strip()
    ra = os.popen(f"grep Aref results/{filename}.log" + " | head -n 2 | tail -n 1 | awk '{print $4}'").read().strip()
    dfs.append(df)
    cds.append(cd)
    ras.append(ra)

df = pd.DataFrame({
    'names': names,
    'length': ls,
    'width': ws,
    'height': hs,
    'noseLength': ns,
    'radius': rs,
    'tailLength': ts,
    'endRadius': es,
    'dragForce': dfs,
    'dragCoeff': cds,
    'refArea': ras})

df.to_csv('result.csv', index=False)
