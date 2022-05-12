import sys
import os
import random
import subprocess
import numpy as np
from copy import deepcopy
import argparse
from absl import app, flags
import csv
from pathlib import Path

from infer import infer
from run_oracle import parse_volume, parse_area
from uuv import *
from helper import gen_stl, parse_json, gen_designs

from py3dbp import Packer, Bin, Item

ranges = [
        {'min':1000, 'max':4000},
        {'min':400, 'max':2000},
        {'min':400, 'max':2000},
        {'min':1000, 'max':4000},
        {'min':200, 'max':1000},
        {'min':1000, 'max':4000},
        {'min':10, 'max':100},
        ]
class Solution:
    def __init__(self, params):
        self.params = params
        self.valid = False
        self.cost = None
        self.true_cost = None
        self.raw_cost = None
        self.raw_true_cost = None
        self.pack_cost = 1.0
        self.buoy_cost = 1.0
        self.df_cost = 1.0
        self.vol_cost = 1.0
        self.df = None
        self.vol = None
        self.area = None
        self.pack = None


class SimulatedAnnealing:
    def __init__(self, sol, n_iter, json_name, sched_method='classic', normalization="none", suffix=None):
        self.normalization = normalization
        self.json_name = json_name.split('/')[-1]
        self.n_iter = n_iter
        self.inner_iter = 5
        self.sol = sol
        self.prev_sol = None
        self.best_sol = None
        self.best_valid_sol = None
        self.alpha = 0.5 # function of temperature
        self.true_cost_w = 0.6 # function of temperature
        self.avg_pack_cost = None
        self.avg_buoy_cost = None
        self.df_cost = None
        self.avg_vol_cost = None
        self.rand_n = 10
        self.t = None
        self.T1 = None
        self.conv_accept_p = 0.02
        self.conv_cnt = 0
        self.sched_method = sched_method
        self.log = []
        self.run_name = f"{self.json_name}_{self.sched_method}_scheduling_{self.normalization}_normalization_{self.n_iter}_iters"
        if suffix is not None: self.run_name += f"_{suffix}"

    def run(self):
        self._init()
        cost, true_cost, raw_cost, raw_true_cost = 0.0, 0.0, 0.0, 0.0
        pvalid = False
        # min_normalized = 1.0
        # min_normalized_true = 1.0
        for i in range(1, self.n_iter+1):

            self.t = self._get_temperature(i, self.sched_method)
            self.avg_delta_cost = 0
            self.avg_accept_p = 0
            success_rate = 0
            pvalid = False
            for j in range(self.inner_iter):
                if pvalid and not valid and random.random() < 1 - accept_p : # change the thing that made it fail with probability 1- accept_p, we want to force valid closer to end of SA
                    perturbed_idx = self._perturb(it=i, idx=perturbed_idx)
                else:
                    perturbed_idx = self._perturb(it=i)

                cost, true_cost, raw_cost, raw_true_cost = self._compute_cost()
                valid = self._is_valid()
                delta_cost = (self.sol.cost - self.prev_sol.cost) * 5
                accept_p = min(1.0, math.exp(-delta_cost / self.t)) if delta_cost != 0 else 0
                # print(delta_cost, accept_p)

                self.avg_delta_cost += abs(delta_cost)

                if self.best_valid_sol is None and valid:
                    self._keep_best_valid()

                if self.normalization == "none":
                    better = cost < self.best_sol.cost
                    if self.best_valid_sol is not None:
                        true_cost_better = true_cost < self.best_valid_sol.true_cost
                elif self.normalization == "best_valid":
                    better = cost < self.best_sol.cost
                    true_cost_better = true_cost < 1 # self.best_valid_sol.true_cost
                    # print(' ', cost, self.best_sol.cost)
                    # print(' ', true_cost, 1) # self.best_valid_sol.true_cost)
                    # print('---', cost, min_normalized)
                    # print('---', true_cost, min_normalized_true)
                    # better = cost < min_normalized
                    # true_cost_better = true_cost < min_normalized_true
                    # min_normalized = min(min_normalized, cost)
                    # min_normalized_true = min(min_normalized_true, true_cost)
                elif self.normalization == "rolling_avg":
                    # raise NotImplementedError("FIXME: rolling average normalization without re-normalizing the current best doesn't make sense!")
                    # print(cost, true_cost)
                    better = cost < 1
                    true_cost_better = true_cost < 1

                if better or random.random() < accept_p:
                    self._keep_prev()
                    if better:
                        self._keep_best()
                    if valid and true_cost_better:
                        # min_normalized = 1.0
                        # min_normalized_true = 1.0
                        self._keep_best_valid()
                else:
                    self._restore_prev()
                pvalid = valid

                self.avg_accept_p += accept_p
                success_rate += valid

            self.avg_delta_cost /= self.inner_iter
            self.avg_accept_p /= self.inner_iter
            success_rate /= self.inner_iter

            self._restore_best()
            self.log.append([self.t, success_rate, self.avg_accept_p, self.avg_delta_cost, self.sol.cost,self.sol.raw_cost, self.sol.true_cost, self.sol.raw_true_cost, self.best_valid_sol.cost,self.best_valid_sol.raw_cost, self.sol.valid, self.sol.df])
            if i % 1 == 0:
                print(f'---- Iter {i} ----')
                print(f'> temperature   : {self.t}')
                print(f'> success rate  : {success_rate}')
                print(f'> avg accept p  : {self.avg_accept_p}')
                print(f'> avg delta cost: {self.avg_delta_cost}')
                print(f'> best params   : {self.sol.params}')
                print(f'> best cost     : {self.sol.cost}')
                print(f'> best cost(raw): {self.sol.raw_cost}')
                print(f'> best true_cost: {self.sol.true_cost}')
                print(f'> best is_valid : {self.sol.valid}')
                print(f'> best placement: {self.sol.pack.items}')
                print(f'> best df       : {self.sol.df}')
                print()
                if self.best_valid_sol is not None:
                    print(f'> best valid params   : {self.best_valid_sol.params}')
                    print(f'> best valid cost     : {self.best_valid_sol.cost}')
                    print(f'> best valid true_cost: {self.best_valid_sol.true_cost}')
                    print(f'> best valid placement: {self.best_valid_sol.pack.items}')
                    print(f'> best valid df       : {self.best_valid_sol.df}')
                    print(f'> best valid vol      : {self.best_valid_sol.vol}')
                else:
                    print('> best valid solution : None')
                print()

            if self._converged(i):
                break

        return self.best_valid_sol


    def _init(self):
        print('Init start')
        temp_sol = deepcopy(self.sol)
        pack_costs = []
        buoy_costs = []
        df_costs = []
        vol_costs = []
        valids = []
        for i in range(self.rand_n):
            self._perturb(it=0)

            df, vol, area = self._evaluate(self.sol)
            self.sol.df = df
            self.sol.vol = vol
            self.sol.area = area

            self.sol.pack = packing_problem(self.sol)
            valid = self._is_valid()

            pack_cost = self._pack_cost()
            buoy_cost = self._buoy_cost()
            df_cost = self._df_cost()
            vol_cost = vol

            pack_costs.append(pack_cost)
            buoy_costs.append(buoy_cost)
            df_costs.append(df_cost)
            vol_costs.append(vol_cost)
            valids.append(valid)

        # import IPython; IPython.embed()
        eps = 1
        self.avg_pack_cost = sum(pack_costs) / len(pack_costs)
        self.avg_pack_cost += eps
        self.avg_buoy_cost = sum(buoy_costs) / len(buoy_costs)
        self.avg_buoy_cost += eps
        self.avg_df_cost = sum(df_costs) / len(df_costs)
        self.avg_df_cost += eps
        self.avg_vol_cost = sum(vol_costs) / len(vol_costs)
        self.avg_vol_cost += eps
        self.accept_rate = sum(valids) / len(valids)

        print(self.avg_pack_cost, self.avg_buoy_cost, self.avg_df_cost, self.avg_vol_cost)

        self.sol = deepcopy(temp_sol)
        self._compute_cost()
        self._keep_prev()
        self._keep_best()

        # uphill_cost = 0
        # uphill_cnt = 0
        # while uphill_cnt < 5:
        #     self._perturb()

        #     cost, true_cost = self._compute_cost()
        #     if cost > self.prev_sol.cost:
        #         uphill_cost += cost - self.prev_sol.cost
        #         uphill_cnt += 1
        #     else:
        #         self._keep_best()

        # self.avg_uphill_cost = uphill_cost / uphill_cnt
        # print(self.avg_uphill_cost)

        # self.sol = deepcopy(temp_sol)
        # self._compute_cost()
        # self._keep_prev()
        # self._keep_best()
        print('Init done')

    def _perturb(self, it, idx=-1):
        lb = max(0.08 - 0.001 * it, 0.04)
        ub = max(0.12 - 0.001 * it, 0.08)
        increase_prob = max(0.4 - 0.005 * it, 0.15)

        # TODO: perturb different dimensions based on failure from last solution?
        if idx != -1 and random.random() < 0.8:
            r = idx
        elif random.random() < 0.2:
            r = np.argmax(self.sol.params)
            increase_prob = 0.2
        else:
            r = random.randint(0, len(ranges)- 1) # lol randint is inclusive on end idx for some reason
        rmin = (ranges[r]['max'] - ranges[r]['min']) * lb # TODO: shud depend on temperature
        rmax = (ranges[r]['max'] - ranges[r]['min']) * ub # TODO: shud depend on temperature
        delta = rmin + (rmax - rmin) * random.random()
        self.sol.params[r] += delta * (1 if random.random() < increase_prob else -1)

        self.sol.params[r] = min(self.sol.params[r], ranges[r]['max'])
        self.sol.params[r] = max(self.sol.params[r], ranges[r]['min'])

        # adjust radius (params[4]) to be less than half of min of length, width, height
        min_dim = min(self.sol.params[0], self.sol.params[1], self.sol.params[2])
        # if min_dim / 2 <= self.sol.params[4]:
        #     self.sol.params[4] = int(min_dim) // 2 - 1
        self.sol.params[4] = min(int(min_dim) // 2 - 1, self.sol.params[4])
        self.sol.params[r] = int(self.sol.params[r])
        return r

    def _is_valid(self):
        if not self.sol.pack.evaluated:
            self.sol.pack.pack()
        pack_valid = self.sol.pack.feasible
        buoy_valid = self.sol.pack.net_in_water_weight <= 0
        df_valid = self.sol.df <= df_threshold
        # print(self.sol.pack.net_in_water_weight)
        # TODO: update success rate?
        if not pack_valid: pass
        if not buoy_valid: pass
        if not df_valid: pass
        self.sol.valid = pack_valid and buoy_valid and df_valid
        return self.sol.valid

    def _pack_cost(self): # TODO this should be normalized / more dynamic
        if not self.sol.pack.evaluated:
            self.sol.pack.pack()
        return self.sol.pack.loss

    def _buoy_cost(self): # TODO: need normalize
        assert self.sol.pack.evaluated
        in_water_weight = self.sol.pack.net_in_water_weight
        return in_water_weight / fairing_density if in_water_weight > 0 else 0

    def _df_cost(self): # TODO: need normalize
        val = max(self.sol.df - df_threshold, 0)
        return val
        #return abs(self.sol.df)

    def _keep_best(self):
        self.best_sol = deepcopy(self.sol)

    def _keep_best_valid(self):
        self.best_valid_sol = deepcopy(self.sol)

    def _keep_prev(self):
        self.prev_sol = deepcopy(self.sol)

    def _restore_best(self):
        self.sol = deepcopy(self.best_sol)

    def _restore_prev(self):
        self.sol = deepcopy(self.prev_sol)

    def _compute_cost(self):
        df, vol, area = self._evaluate(self.sol)
        self.sol.df = df
        self.sol.vol = vol
        self.sol.area = area

        self.sol.pack = packing_problem(self.sol)
        self.sol.pack_cost = self._pack_cost()
        self.sol.buoy_cost = self._buoy_cost()
        self.sol.df_cost = self._df_cost()
        self.sol.vol_cost = vol
        if self.normalization == "best_valid" and self.best_valid_sol is not None:
            # pack_cost_normalized = self.sol.pack_cost / max(1, self.best_valid_sol.pack_cost)
            # buoy_cost_normalized = self.sol.buoy_cost / max(1, self.best_valid_sol.buoy_cost)
            # df_cost_normalized = self.sol.df_cost / max(1, self.best_valid_sol.df_cost) # is this ever under 1?
            pack_cost_normalized = self.sol.pack_cost / self.avg_pack_cost
            buoy_cost_normalized = self.sol.buoy_cost / self.avg_buoy_cost
            df_cost_normalized = self.sol.df_cost / self.avg_df_cost
            vol_cost_normalized = self.sol.vol_cost / max(1, self.best_valid_sol.vol_cost)
        elif self.normalization == "rolling_avg":
            pack_cost_normalized = self.sol.pack_cost / self.avg_pack_cost
            buoy_cost_normalized = self.sol.buoy_cost / self.avg_buoy_cost
            df_cost_normalized = self.sol.df_cost / self.avg_df_cost
            vol_cost_normalized = self.sol.vol_cost / self.avg_vol_cost
        elif self.normalization == "none" or self.best_valid_sol is None:
            pack_cost_normalized = self.sol.pack_cost / self.avg_pack_cost
            buoy_cost_normalized = self.sol.buoy_cost / self.avg_buoy_cost
            df_cost_normalized = self.sol.df_cost / self.avg_df_cost
            vol_cost_normalized = self.sol.vol_cost / self.avg_vol_cost
        # print(self.sol.pack_cost_normalized, buoy_cost_normalized, df_cost_normalized, vol_cost_normalized)

        cost, true_cost = self._cost_fun(pack_cost_normalized, buoy_cost_normalized, df_cost_normalized, vol_cost_normalized)
        raw_cost, raw_true_cost = self._cost_fun(self.sol.pack_cost, self.sol.buoy_cost, self.sol.df_cost, self.sol.vol_cost)

        self.sol.cost = cost
        self.sol.true_cost = true_cost
        self.sol.raw_cost = raw_cost
        self.sol.raw_true_cost = raw_true_cost

        if self.normalization == "rolling_avg":
            self._update_avg(self.sol.pack_cost, self.sol.buoy_cost, self.sol.df_cost, self.sol.vol_cost)
        return cost , true_cost, raw_cost, raw_true_cost# TODO implement hard enforcement

    def _cost_fun(self, pack_cost_norm, buoy_cost_norm, df_cost_norm, vol_cost_norm):
        true_cost = vol_cost_norm
        # TODO: can do some weighting
        feasible_cost = (pack_cost_norm + df_cost_norm + buoy_cost_norm) / 3
        # if self.normalization in ["none", "best_valid"] and self.t is not None:
        if self.t is not None:
            feasible_cost *= (1 + min(4, 1 / self.t))
        cost = self.true_cost_w * true_cost + (1-self.true_cost_w) * feasible_cost
        # if self.normalization == "none" or self.best_valid_sol is None: # deals with overflow
        #     return math.log10(cost), math.log10(true_cost)
        # else:
        #     return cost , true_cost
        return cost , true_cost

    def _evaluate(self, sol):
        p = sol.params
        df = infer(p)
        gen_stl(*p)
        vol = parse_volume()
        area = parse_area()
        return df, vol, area

    def _converged(self, it):
        if self.avg_accept_p < self.conv_accept_p:
            self.conv_cnt += 1
        else:
            self.conv_cnt = 0
        return self.conv_cnt >= 1 or it >= 150

    def _update_avg(self, pack_cost, buoy_cost, df_cost, vol_cost):
        assert self.avg_pack_cost is not None
        assert self.avg_buoy_cost is not None
        assert self.avg_df_cost is not None
        self.avg_pack_cost = (self.avg_pack_cost * (self.rand_n-1) + pack_cost) / self.rand_n
        self.avg_buoy_cost = (self.avg_buoy_cost * (self.rand_n-1) + buoy_cost) / self.rand_n
        self.avg_df_cost = (self.avg_df_cost * (self.rand_n-1) + df_cost) / self.rand_n
        self.avg_vol_cost = (self.avg_vol_cost * (self.rand_n-1) + vol_cost) / self.rand_n
        # print(self.avg_pack_cost, self.avg_buoy_cost, self.avg_df_cost, self.avg_vol_cost)


    def _get_temperature(self, it, scheduling_method='classic'):
        # constants
        lmbda = 0.85
        lmbda_lb = 0.8
        lmbda_ub = 0.95
        num_local_search_iter = 20
        c = 5

        new_t = None
        if it == 1:
            print("init accept rate:", self.accept_rate)
            new_t = 1e2 / (-math.log(min(0.8, self.accept_rate + 1e-2))) # TODO: change this
            # new_t = self.avg_uphill_cost / (-math.log(min(0.9, self.accept_rate + 1e-2))) # TODO: change this
            # new_t = 0.01 / (-math.log(min(0.9, self.accept_rate + 1e-2))) # TODO: change this
            self.T1 = new_t
        elif scheduling_method == 'classic':
            new_t = self.t * lmbda
        elif scheduling_method == 'timberwolf':
            if it < self.n_iter / 2:
                lmbda = lmbda_lb + (it - 1) / (self.n_iter / 2) * (lmbda_ub - lmbda_lb)
            if it >= self.n_iter / 2:
                lmbda = lmbda_ub - (it - self.n_iter / 2) / (self.n_iter / 2) * (lmbda_ub - lmbda_lb)
            new_t = self.t * lmbda
        elif scheduling_method == 'fast':
            if it <= num_local_search_iter:
                new_t = self.T1 * self.avg_delta_cost / it / c
            else:
                new_t = self.T1 * self.avg_delta_cost / it
        return new_t

    def write(self):
        Path("logs").mkdir(parents=True, exist_ok=True)
        with open(f"logs/{self.run_name}_log.csv", 'w') as log_file:
            output = csv.writer(log_file) # TODO add cost normalization method
            output.writerow(["t", "success_rate", "avg_accept_p", "avg_delta_cost", "sol_cost","sol_raw_cost", "sol_true_cost", "sol_raw_true_cost", "best_valid_sol_cost","best_valid_sol_raw_cost", "sol_valid", "sol_df"])
            for line in self.log:
                output.writerow(line)
        with open(f"logs/{self.run_name}_results.csv", 'w') as results_file:
            output = csv.writer(results_file) # TODO add cost normalization method
            output.writerow(["length", "width", "height", "noseLength", "radius", "tailLength", "endRadius"])
            output.writerow(self.best_valid_sol.params)

    def visualize(self, sol):
        gen_designs(sol, self.run_name)





def main(args):
    # if len(sys.argv[1:]) != 7:
    #     print('invalid number of arguments, defaulting...')
    #     args = [int(i) for i in "50000 2000 2000 10 5 10 5".split()]
    # else:
    #     args = [int(arg) for arg in sys.argv[1:]]
    params = parse_json(FLAGS.json)
    sol = Solution(params)
    niters = 2
    sa = SimulatedAnnealing(sol, niters, FLAGS.json, FLAGS.sched, FLAGS.norm, FLAGS.suffix)
    best_valid_sol = sa.run()
    if FLAGS.log:
        sa.write()
    if FLAGS.visual:
        sa.visualize(best_valid_sol)

if __name__ == '__main__':
    FLAGS = flags.FLAGS
    flags.DEFINE_string('json', None, 'Input design (as json)')
    flags.DEFINE_enum(
            'sched',
            'classic',
            ['classic', 'timberwolf', 'fast'],
            'Temperature scheduling method for SA',
            )
    flags.DEFINE_enum(
            'norm',
            'none',
            ['none', 'rolling_avg', 'best_valid'],
            'Cost normalization method for SA',
            )
    flags.DEFINE_boolean("log", False, "Write out log and assignment")
    flags.DEFINE_boolean("visual", False, "Create files for visualization")
    flags.DEFINE_string('suffix', None, 'Suffix added to output files')

    flags.mark_flag_as_required('json')
    app.run(main)
