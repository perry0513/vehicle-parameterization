set datafile separator ','
set ytics nomirror
set y2tics

set autoscale  y
set autoscale y2
set ylabel "cost"
set y2label "raw cost"
set key autotitle columnhead

plot "logs/test.json_classic_scheduling_best_valid_normalization_20_iters_log.csv" using 5 axis x1y1 title "cost" w lines, "logs/test.json_classic_scheduling_best_valid_normalization_20_iters_log.csv" using 6 axis x1y2 title "raw cost" w lines
