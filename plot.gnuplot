norm_names = "none best_valid rolling_avg"
sched_names = "classic timberwolf fast"
do for [i=1:words(norm_names)] {
files = "logs/test.json_classic_scheduling_".word(norm_names, i)."_normalization_200_iters_1_log.csv logs/test.json_timberwolf_scheduling_".word(norm_names, i)."_normalization_200_iters_1_log.csv logs/test.json_fast_scheduling_".word(norm_names, i)."_normalization_200_iters_1_log.csv"


set datafile separator ','
set ytics nomirror
set terminal png size 800,700;
set output "figs/all_cost_scheduling_norm_".word(norm_names, i).".png"

set autoscale  y
set ylabel "Raw Cost (Best Valid)"
set key autotitle columnhead
set title "Raw cost over Iterations by Scheduling (Normalization: ".word(norm_names,i)

plot word(files,1) using 10 axis x1y1 title word(sched_names,1)." raw cost" w lines, word(files, 2) using 10 axis x1y1 w lines title word(sched_names, 2)."raw cost", word(files, 3) using 10 axis x1y1 w lines title word(sched_names, 3)." raw cost"


do for [t=1:words(files)] {

set terminal png size 800,700;
set output "figs/".word(sched_names,t)."_cost_temp_scheduling_".word(norm_names,i)."_normalization.png"

set autoscale  y
set autoscale y2
set ylabel "Raw Cost (Best Valid)"
set y2label "Temperature"
set key autotitle columnhead
set title "Raw cost and Temperature over Iterations (".word(sched_names,t)." Scheduling, Normalization: ".word(norm_names,i).")"

plot word(files,t) using 10 axis x1y1 title "raw cost" w lines, \
word(files,t) using 1 axis x1y2 title "temp" w lines

}
}
