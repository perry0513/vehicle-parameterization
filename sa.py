import sys
import random
import subprocess

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
    def __init__(params):
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
        self.best_cost = self._compute_cost()

    def run(self):
        self.sol = self.best_sol
        for i in range(self.n_iter):
            t = self._get_temperature(i)
            p = self._get_prob(t)
            for j in range(self.inner_iter):
                self._perturb()
                cost, true_cost = self._compute_cost()
                valid = self._is_valid()

                if self.best_valid_sol is None and valid:
                    self._keep_best_valid()

                if (valid and cost < self.best_cost) or random.random() < p:
                    self.keep_prev()
                    if cost < self.best_cost:
                        self._keep_best()
                    if valid and true_cost < self.best_valid_sol.true_cost:
                        self._keep_best_valid()
                else:
                    self._restore_prev()

            self._restore_best()

        return self.best_valid_sol


    def _perturb(self):
        r = random.randint(0, len(ranges))
        rmin = (ranges[r]['max'] - ranges[r]['min']) * 0.05
        rmax = (ranges[r]['max'] - ranges[r]['min']) * 0.10
        delta = rmin + (rmax - rmin) * random.random()
        self.sol.params[r] += delta * (1 if random.random() < 0.5 else -1)

    def _is_valid(self):
        vol_check = self.sol.vol > self.vol_threshold
        payload_check = \
                   (self.sol.params[0] > payload_x and self.sol.params[1] > payload_y and self.sol.params[2] > payload_z) \
                or (self.sol.params[0] > payload_x and self.sol.params[2] > payload_y and self.sol.params[1] > payload_z) \
                or (self.sol.params[1] > payload_x and self.sol.params[0] > payload_y and self.sol.params[2] > payload_z) \
                or (self.sol.params[1] > payload_x and self.sol.params[2] > payload_y and self.sol.params[0] > payload_z) \
                or (self.sol.params[2] > payload_x and self.sol.params[0] > payload_y and self.sol.params[1] > payload_z) \
                or (self.sol.params[2] > payload_x and self.sol.params[1] > payload_y and self.sol.params[0] > payload_z)
        df_check = self.sol.df < self.df_threshold

        self.sol.valid = vol_check and payload_check and df_check

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
        if self.sol.df is None:
            df, vol = self._evaluate_sol(self.sol)
            self.sol.df = df
            self.sol.vol = vol

        cost = # TODO exponential from _expo_packing + drag
        true_cost = # TODO inf if _expo_packing nonzero + drag

        self.sol.cost = cost
        self.sol.true_cost = true_cost

        return cost, true_cost


    def _evaluate(self, sol):
        p = sol.params
        cmd = f'python3 infer.py {p[0]} {p[1]} {p[2]} {p[3]} {p[4]} {p[5]} {p[6]}'
        df_str = subprocess.check_output(cmd.split(' ')).decode('utf-8')
        cmd = f'./run_oracle vol {p[0]} {p[1]} {p[2]} {p[3]} {p[4]} {p[5]} {p[6]}'
        vol_str = subprocess.check_output(cmd.split(' ')).decode('utf-8')
        return float(df_str), float(vol_str)

    def _get_temperature(self, it):
        pass

    def _get_prob(self, t):
        pass


if __name__ == '__main__':
    args = [float(arg) for arg in sys.argv[1:]]
    init_sol = Solution(args)
    sa = SimulatedAnnealing(init_sol, 5)
    sa.run()
