import sys
import os
import random
import subprocess
import numpy as np
from copy import deepcopy

from infer import infer
from run_oracle import gen_stl, parse_volume, parse_area
from uuv import *


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
        self.cost = 1000000
        self.true_cost = 1000000
        self.df = None
        self.vol = None
        self.area = None


class SimulatedAnnealing:
    def __init__(self, sol, n_iter):
        self.n_iter = n_iter
        self.inner_iter = 5
        self.sol = sol
        self.prev_sol = deepcopy(sol)
        self.best_sol = deepcopy(sol)
        self.best_valid_sol = None
        self.alpha = 0.5 # function of temperature
        self.beta = 0.5 # function of temperature

    def run(self):
        self.sol = self.best_sol
        cost, true_cost = 0.0, 0.0
        for i in range(self.n_iter):
            t = self._get_temperature(i)
            p = self._get_prob(t)
            for j in range(self.inner_iter):
                self._perturb()
                cost, true_cost = self._compute_cost()
                valid = self._is_valid()

                if self.best_valid_sol is None and valid:
                    self._keep_best_valid()

                if cost < self.best_sol.cost or random.random() < p:
                    self._keep_prev()
                    if cost < self.best_sol.cost:
                        self._keep_best()
                    if valid and true_cost < self.best_valid_sol.true_cost:
                        self._keep_best_valid()
                else:
                    self._restore_prev()

            self._restore_best()
            if i % 1 == 0:
                print(f'---- Iter {i} ----')
                print(f'> best params   : {self.sol.params}')
                print(f'> best cost     : {self.sol.cost}')
                print(f'> best true_cost: {self.sol.true_cost}')
                print(f'> best is_valid : {self.sol.valid}')
                print(f'> best df       : {self.sol.df}')
                print()
                if self.best_valid_sol is not None:
                    print(f'> best valid params   : {self.best_valid_sol.params}')
                    print(f'> best valid cost     : {self.best_valid_sol.cost}')
                    print(f'> best valid true_cost: {self.best_valid_sol.true_cost}')
                    print(f'> best valid df       : {self.best_valid_sol.df}')
                else:
                    print('> best valid solution : None')

        return self.best_valid_sol


    def _perturb(self):
        r = random.randint(0, len(ranges)- 1) # lol randint is inclusive on end idx for some reason
        rmin = (ranges[r]['max'] - ranges[r]['min']) * 0.05
        rmax = (ranges[r]['max'] - ranges[r]['min']) * 0.10
        delta = rmin + (rmax - rmin) * random.random()
        self.sol.params[r] += delta * (1 if random.random() < 0.5 else -1)
        
        self.sol.params[r] = min(self.sol.params[r], ranges[r]['max'])
        self.sol.params[r] = max(self.sol.params[r], ranges[r]['min'])

        # adjust radius (params[4]) to be less than half of min of length, width, height
        min_dim = min(self.sol.params[0], self.sol.params[1], self.sol.params[2])
        if min_dim / 2 <= self.sol.params[4]:
            self.sol.params[4] = int((min_dim-1) / 2)
        self.sol.params[r] = int(self.sol.params[r])

    def _is_valid(self):
        payload_check = \
                   (self.sol.params[0] > payload_x and self.sol.params[1] > payload_y and self.sol.params[2] > payload_z) \
                or (self.sol.params[0] > payload_x and self.sol.params[2] > payload_y and self.sol.params[1] > payload_z) \
                or (self.sol.params[1] > payload_x and self.sol.params[0] > payload_y and self.sol.params[2] > payload_z) \
                or (self.sol.params[1] > payload_x and self.sol.params[2] > payload_y and self.sol.params[0] > payload_z) \
                or (self.sol.params[2] > payload_x and self.sol.params[0] > payload_y and self.sol.params[1] > payload_z) \
                or (self.sol.params[2] > payload_x and self.sol.params[1] > payload_y and self.sol.params[0] > payload_z)
        df_check = self.sol.df < df_threshold
        self.sol.valid = payload_check and df_check

        return self.sol.valid

    def _packing_cost(self):
       val = min((min(self.sol.params[0] - payload_x, 0) ** 2 + min(self.sol.params[1] - payload_y, 0) ** 2 + min(self.sol.params[2] - payload_z, 0) ** 2), \
                 (min(self.sol.params[0] - payload_x, 0) ** 2 + min(self.sol.params[2] - payload_y, 0) ** 2 + min(self.sol.params[1] - payload_z, 0) ** 2), \
                 (min(self.sol.params[1] - payload_x, 0) ** 2 + min(self.sol.params[0] - payload_y, 0) ** 2 + min(self.sol.params[2] - payload_z, 0) ** 2), \
                 (min(self.sol.params[1] - payload_x, 0) ** 2 + min(self.sol.params[2] - payload_y, 0) ** 2 + min(self.sol.params[0] - payload_z, 0) ** 2), \
                 (min(self.sol.params[2] - payload_x, 0) ** 2 + min(self.sol.params[0] - payload_y, 0) ** 2 + min(self.sol.params[1] - payload_z, 0) ** 2), \
                 (min(self.sol.params[2] - payload_x, 0) ** 2 + min(self.sol.params[1] - payload_y, 0) ** 2 + min(self.sol.params[0] - payload_z, 0) ** 2))

       return val

    def _df_cost(self):
        val = max(self.sol.df - df_threshold, 0)
        return val


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
        packing_cost = self._packing_cost()
        packing_cost_normalized = packing_cost
        df_cost = self._df_cost()
        df_cost_normalized = df_cost

        true_cost = self.sol.vol
        cost = self.alpha * packing_cost_normalized + (1-self.alpha) * df_cost_normalized
        cost = self.beta * true_cost + (1-self.beta) * cost

        self.sol.cost = cost
        self.sol.true_cost = true_cost

        return cost , true_cost # TODO implement hard enforcement


    def _evaluate(self, sol):
        p = sol.params
        df = infer(p)
        gen_stl(*p)
        vol = parse_volume()
        area = parse_area()
        return df, vol, area


    def _get_temperature(self, it):
        return 0 if not it else self.n_iter / it   # TODO bruh

    def _get_prob(self, t):
        return .25 #TODO dynamic


if __name__ == '__main__':
    args = [int(arg) for arg in sys.argv[1:]]
    sol = Solution(args)
    sa = SimulatedAnnealing(sol, 1000)
    sa.run()
