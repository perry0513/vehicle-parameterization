import sys
import os
import random
import subprocess
import numpy as np
payload_x = 1000
payload_y = 1000
payload_z = 300

ranges = [
        {'min':1000, 'max':4000},
        {'min':400, 'max':2000},
        {'min':400, 'max':2000},
        {'min':200, 'max':1000},
        {'min':1000, 'max':4000},
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


class SimulatedAnnealing:
    def __init__(self, sol, n_iter):
        self.n_iter = n_iter
        self.inner_iter = 5
        self.sol = sol
        self.prev_sol = sol
        self.best_sol = sol
        self.best_valid_sol = None
        self.best_cost = float('inf')

    def run(self):
        self.sol = self.best_sol
        cost, true_cost = 0.0, 0.0
        for i in range(self.n_iter):
            t = self._get_temperature(i)
            p = self._get_prob(t)
            for j in range(self.inner_iter):
                self._perturb()
                cost, true_cost = self._compute_cost()
                valid = not self._is_valid()

                if self.best_valid_sol is None and valid:
                    self._keep_best_valid()

                # print(cost, self.best_cost, random.random(), p)
                if (cost < self.best_cost) or random.random() < p:
                    self._keep_prev()
                    if cost < self.best_cost:
                        self._keep_best()
                    if valid and true_cost < self.best_valid_sol.true_cost:
                        print(self.sol)
                        self._keep_best_valid()
                else:
                    self._restore_prev()

            self._restore_best()
            if i % 20 == 0:
                print(self.sol.params)
                print(self.sol.cost, self.sol.true_cost)

        return self.best_valid_sol


    def _perturb(self):
        # if index is 4, it needs to be min of all
        r = random.randint(0, len(ranges)- 1) # lol randint is inclusive on end idx for some reason
        rmin = (ranges[r]['max'] - ranges[r]['min']) * 0.05
        rmax = (ranges[r]['max'] - ranges[r]['min']) * 0.10
        delta = rmin + (rmax - rmin) * random.random()
        if r != 4:
       # if r != 4 and r != 6:
            self.sol.params[r] += delta * (1 if random.random() < 0.5 else -1)
        else:
            #self.sol.params[r] = min(self.sol.params[r] + delta * (1 if random.random() < 0.5 else -1), min(self.sol.params))
            # lol idk, radius being not the smallest will break sim
            # TODO radius should still be purturbed, but there needs to be checks
            pass
        self.sol.params[r] = abs(self.sol.params[r]) # TODO This is bad probably, neg params don't make sense tho

    def _is_valid(self):
        payload_check = \
                   (self.sol.params[0] > payload_x and self.sol.params[1] > payload_y and self.sol.params[2] > payload_z) \
                or (self.sol.params[0] > payload_x and self.sol.params[2] > payload_y and self.sol.params[1] > payload_z) \
                or (self.sol.params[1] > payload_x and self.sol.params[0] > payload_y and self.sol.params[2] > payload_z) \
                or (self.sol.params[1] > payload_x and self.sol.params[2] > payload_y and self.sol.params[0] > payload_z) \
                or (self.sol.params[2] > payload_x and self.sol.params[0] > payload_y and self.sol.params[1] > payload_z) \
                or (self.sol.params[2] > payload_x and self.sol.params[1] > payload_y and self.sol.params[0] > payload_z)
        self.sol.valid = payload_check

        return self.sol.valid
    def _expo_packing(self):
       val = max(0, min(self.sol.params[0] - payload_x,0) + min(0, self.sol.params[1] - payload_y) + min(0, self.sol.params[2] - payload_z), \
                   (min(self.sol.params[0] - payload_x,0) + min(0, self.sol.params[2] - payload_y) + min(0, self.sol.params[1] - payload_z)), \
                   (min(self.sol.params[1] - payload_x,0) + min(0, self.sol.params[0] - payload_y) + min(0, self.sol.params[2] - payload_z)), \
                   (min(self.sol.params[1] - payload_x,0) + min(0, self.sol.params[2] - payload_y) + min(0, self.sol.params[0] - payload_z)), \
                   (min(self.sol.params[2] - payload_x,0) + min(0, self.sol.params[0] - payload_y) + min(0, self.sol.params[1] - payload_z)), \
                   (min(self.sol.params[2] - payload_x,0) + min(0, self.sol.params[1] - payload_y) + min(0, self.sol.params[0] - payload_z)))

       return np.power(val, 2)


    def _keep_best(self):
        self.best_sol = self.sol

    def _keep_best_valid(self):
        self.best_valid_sol = self.sol

    def _keep_prev(self):
        self.prev_sol = self.sol

    def _restore_best(self):
        self.sol = self.best_sol

    def _restore_prev(self):
        self.sol = self.prev_sol

    def _compute_cost(self):
        # if self.sol.df is None:
        if True:
            df, vol = self._evaluate(self.sol)
            self.sol.df = df
            self.sol.vol = vol

        fits = self._expo_packing()
        cost = np.exp(fits) + self.sol.df
        true_cost = float('inf') if fits else self.sol.df

        self.sol.cost = cost
        self.sol.true_cost = true_cost

        return cost , true_cost # TODO implement hard enforcement


    def _evaluate(self, sol):
        p = sol.params
        cmd = f'python3 infer.py {p[0]} {p[1]} {p[2]} {p[3]} {p[4]} {p[5]} {p[6]}'
        df_str = subprocess.check_output(cmd.split(' ')).decode('utf-8')
        cmd = f'./run_oracle vol {p[0]} {p[1]} {p[2]} {p[3]} {p[4]} {p[5]} {p[6]}'
        vol_str = subprocess.check_output(cmd.split(' ')).decode('utf-8')
        return float(df_str), float(vol_str)


    def _get_temperature(self, it):
        return 0 if not it else self.n_iter / it   # TODO bruh

    def _get_prob(self, t):
        return .25 #TODO dynamic


if __name__ == '__main__':
    args = [float(arg) for arg in sys.argv[1:]]
    init_sol = Solution(args)
    sa = SimulatedAnnealing(init_sol, 1000)
    sa.run()
