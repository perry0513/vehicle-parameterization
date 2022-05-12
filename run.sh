scheds="classic timberwolf fast"
norms="none best_valid rolling_avg"
for norm in $norms; do
    for sched in $scheds; do
        for i in {1..5}; do 
            python sa.py --json $1 --sched $sched --norm $norm --log --visual --suffix $i
        done
    done
done
