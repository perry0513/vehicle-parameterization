import sys
import os
import random
import subprocess
import numpy as np
from copy import deepcopy

from infer import infer
from run_oracle import gen_stl, parse_volume, parse_area
from uuv import *

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
        self.df = None
        self.vol = None
        self.area = None
        self.pack = None


class SimulatedAnnealing:
    eps = 0.001
    def __init__(self, sol, n_iter, scheduling_method):
        self.scheduling_method = scheduling_method
        self.n_iter = n_iter
        self.inner_iter = 5
        self.sol = sol
        self.prev_sol = None
        self.best_sol = None
        self.best_valid_sol = None
        self.alpha = 0.5 # function of temperature
        self.beta = 0.5 # function of temperature
        self.avg_pack_cost = None
        self.avg_buoy_cost = None
        self.df_cost = None
        self.avg_vol_cost = None
        self.rand_n = 10
        self.t = None
        self.T1 = None

    def run(self):
        self._init()
        cost, true_cost = 0.0, 0.0
        pvalid = False
        for i in range(1, self.n_iter+1):

            self.t = self._get_temperature(i, scheduling_method=self.scheduling_method)
            self.avg_delta_cost = 0
            # print(self.t)
            a = []
            for j in range(self.inner_iter):
                cost, true_cost = self._compute_cost()
                valid = self._is_valid()
                delta_cost = self.sol.cost - self.prev_sol.cost
                accept_p = min(1.0, math.exp(-delta_cost / self.t))
                # print(accept_p)
#                if pvalid and not valid and random.random() < 1- accept_p : # change the thing that made it fail with probability 1- accept_p, we want to force valid closer to end of SA
#                    perturbed_idx = self._perturb(idx=perturbed_idx)
#                else:
                perturbed_idx = self._perturb()

                self.avg_delta_cost += abs(delta_cost)
                if valid:
                    a.append([cost, true_cost])
                else:
                    a.append([self.prev_sol.cost, self.prev_sol.true_cost])
              #  print(self.sol.params)

                if self.best_valid_sol is None and valid:
                    self._keep_best_valid()
              #  print(cost, self.best_sol.cost)

                if cost < self.best_sol.cost or random.random() < accept_p:
                    self._keep_prev()
                    if cost < self.best_sol.cost:
                        self._keep_best()
                    if valid and true_cost < self.best_valid_sol.true_cost:
                        self._keep_best_valid()
                else:
                    self._restore_prev()
                pvalid = valid

            self._restore_best()
            if i % 1 == 0:
                print(f'---- Iter {i} ----')
                print(f'> avg delta cost: {self.avg_delta_cost}')
                print(f'> best params   : {self.sol.params}')
                print(f'> best cost     : {self.sol.cost}')
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
                else:
                    print('> best valid solution : None')
                print()

            self.avg_delta_cost /= self.inner_iter
        #print(self.best_valid_sol)
        return self.best_valid_sol, a


    def _init(self):
        print('Init start')
        temp_sol = deepcopy(self.sol)
        pack_costs = []
        buoy_costs = []
        df_costs = []
        vol_costs = []
        valids = []
        for i in range(self.rand_n):
            self._perturb(init=True)

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
        eps = 1e-4
        self.avg_pack_cost = sum(pack_costs) / len(pack_costs)
        self.avg_pack_cost += eps
        self.avg_buoy_cost = sum(buoy_costs) / len(buoy_costs)
        self.avg_buoy_cost += eps
        self.avg_df_cost = sum(df_costs) / len(df_costs)
        self.avg_df_cost += eps
        self.avg_vol_cost = sum(vol_costs) / len(vol_costs)
        self.avg_vol_cost += eps
        self.accept_rate = sum(valids) / len(valids)

        self.sol = deepcopy(temp_sol)
        self._compute_cost()
        self._keep_prev()
        self._keep_best()
        print('Init done')

    def _perturb(self, init=False, idx=-1):
        # TODO: perturb different dimensions based on failure from last solution?

        if idx == -1:
            r = random.randint(0, len(ranges)- 1) # lol randint is inclusive on end idx for some reason
        else:
            r = idx
        rmin = (ranges[r]['max'] - ranges[r]['min']) * 0.05 # TODO: shud depend on temperature
        rmax = (ranges[r]['max'] - ranges[r]['min']) * 0.10 # TODO: shud depend on temperature
        delta = rmin + (rmax - rmin) * random.random()
        self.sol.params[r] += delta * (1 if random.random() < 0.5 else -1)

        self.sol.params[r] = min(self.sol.params[r], ranges[r]['max'])
        self.sol.params[r] = max(self.sol.params[r], ranges[r]['min'])

        # adjust radius (params[4]) to be less than half of min of length, width, height
        min_dim = min(self.sol.params[0], self.sol.params[1], self.sol.params[2])
        if min_dim / 2 <= self.sol.params[4]:
            self.sol.params[4] = int((min_dim-1) / 2)
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
        return in_water_weight if in_water_weight > 0 else 0

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

        # TODO: normalize cost
        self.sol.pack = packing_problem(self.sol)
        pack_cost = self._pack_cost()
        pack_cost_normalized = pack_cost / self.avg_pack_cost
        buoy_cost = self._buoy_cost()
        buoy_cost_normalized = buoy_cost / self.avg_buoy_cost
        df_cost = self._df_cost()
        df_cost_normalized = df_cost / self.avg_df_cost
        vol_cost = vol
        vol_cost_normalized = vol_cost / self.avg_vol_cost
        # print(pack_cost_normalized, buoy_cost_normalized, df_cost_normalized, vol_cost_normalized)

        true_cost = vol_cost_normalized
        # TODO: can do some weighting
        feasible_cost = (pack_cost_normalized + df_cost_normalized + buoy_cost_normalized) / 3
        cost = self.beta * true_cost + (1-self.beta) * feasible_cost

        self.sol.cost = cost
        self.sol.true_cost = true_cost

        self._update_avg(pack_cost, buoy_cost, df_cost, vol_cost)

        return cost , true_cost # TODO implement hard enforcement


    def _evaluate(self, sol):
        p = sol.params
        df = infer(p)
        gen_stl(*p)
        vol = parse_volume()
        area = parse_area()
        return df, vol, area

    def _update_avg(self, pack_cost, buoy_cost, df_cost, vol_cost):
        assert self.avg_pack_cost is not None
        assert self.avg_buoy_cost is not None
        assert self.avg_df_cost is not None
        self.avg_pack_cost = (self.avg_pack_cost * (self.rand_n-1) + pack_cost) / self.rand_n
        self.avg_buoy_cost = (self.avg_buoy_cost * (self.rand_n-1) + buoy_cost) / self.rand_n
        self.avg_df_cost = (self.avg_df_cost * (self.rand_n-1) + df_cost) / self.rand_n
        self.avg_vol_cost = (self.avg_vol_cost * (self.rand_n-1) + vol_cost) / self.rand_n


    def _get_temperature(self, it, scheduling_method='classic'):
        # constants
        lmbda = 0.85
        lmbda_lb = 0.8
        lmbda_ub = 0.95
        c = 5

        new_t = None
        if it == 1:
            new_t = 1e5 / (-math.log(self.accept_rate + 1e-3)) # TODO: change this
            self.T1 = new_t
        elif scheduling_method == 'classic':
            new_t = self.t * lmbda
        elif scheduling_method == 'timberwolf':
            if it < self.iter / 2:
                new_t = lmbda_lb + (it - 1) / (self.iter / 2) * (lmbda_ub - lmbda_lb)
            if it >= self.iter / 2:
                new_t = lmbda_ub - (it - self.iter / 2) / (self.iter / 2) * (lmbda_ub - lmbda_lb)
            new_t = self.t * lmbda
        elif scheduling_method == 'fast':
            if it <= num_local_search_iter:
                new_t = self.T1 * self.avg_delta_cost / it / c
            else:
                new_t = self.T1 * self.avg_delta_cost / it
        return new_t


if __name__ == '__main__':
    b = []
    for idx, schedule in enumerate(['classic', 'timberwolf', 'fast']):
        if len(sys.argv[1:]) != 7:
            print('invalid number of arguments, defaulting...')
            args = [int(i) for i in "50000 2000 2000 10 5 10 5".split()]
        else:
            args = [int(arg) for arg in sys.argv[1:]]
        sol = Solution(args)
        niters = 4
        sa = SimulatedAnnealing(sol, niters, schedule)
        best, a = sa.run()
        b.append(a)
        with open('outputs.txt', 'a') as f:
            f.writelines(f"best for {schedule} run for {niters} iterations: {best.params}, with cost {best.cost}")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1,3, figsize=(7,15))
    idx = 0
    for idx, schedule in enumerate(['classic', 'timberwolf', 'fast']):
        axs[idx].set_title(f"{schedule} scheduling, abs and normalized cost, {niters} outer iterations")
        color = 'tab:red'
        axs[idx].set_xlabel("outer iterations")
        axs[idx].set_ylabel("normalized cost", color=color)
        axs[idx].plot([i[0] for i in b[idx]], color=color)
        axs[idx].tick_params(axis='y', labelcolor=color)
        ax2= axs[idx].twinx()
        color = 'tab:blue'
        ax2.set_ylabel("normalized true cost", color=color)
        ax2.plot([i[1] for i in b[idx]], color=color)
        ax2.tick_params(axis='y', labelcolor=color)
    fig.savefig('temp.png', dpi=fig.dpi)
