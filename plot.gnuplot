set datafile separator ','
set ytics nomirror
set y2tics
set terminal png size 800,700;
set output "cost_scheduling.png"

set autoscale  y
set autoscale y2
set ylabel "Raw Cost"
set y2label "Temperature"
set key autotitle columnhead
set title "Raw cost over Iterations by Scheduling"

classic = "logs/test.json_classic_scheduling_none_normalization_200_iters_1_log.csv"
timberwolf = "logs/test.json_timberwolf_scheduling_none_normalization_200_iters_1_log.csv"
fast = "logs/test.json_fast_scheduling_none_normalization_200_iters_1_log.csv"

plot classic using 6 axis x1y1 title "classic raw cost" w lines, timberwolf using 6 axis x1y1 w lines title "timberwolf raw cost", fast using 6 axis x1y1 w lines title "fast raw cost",\
classic using 1 axis x1y2 title "classic temp" w lines, timberwolf using 1 axis x1y2 w lines title "timberwolf temp", fast using 1 axis x1y2 w lines title "fast temp"
