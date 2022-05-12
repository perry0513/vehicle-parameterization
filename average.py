import csv
import pandas as pd
from operator import add
norm_names = "none best_valid rolling_avg".split()
sched_names = "classic timberwolf fast".split()
for norm in norm_names:
    for sched in sched_names:
        log = pd.read_csv(f"logs/test.json_{sched}_scheduling_{norm}_normalization_200_iters_1_log.csv")
        avgc = (log["best_valid_sol_raw_cost"].tolist())
        avgt = (log["t"].tolist())
        for it in range(2,5):
            log = pd.read_csv(f"logs/test.json_{sched}_scheduling_{norm}_normalization_200_iters_{it}_log.csv")
            avgc = list(map(add, avgc, log["best_valid_sol_raw_cost"].tolist()))
            avgc = list(map(add, avgt, log["t"].tolist()))
        with open(f"logs/test.json_{sched}_scheduling_{norm}_normalization_200_iters_avg_log.csv", 'w') as f:
            writ = csv.writer(f, delimiter=',')
            writ.writerow(['t', 'best_valid_sol_raw_cost'])
            for i in range(len(avgc)):
                writ.writerow([avgc[i] / 5.0, avgt[i] / 5.0]) # lol averaging moment
