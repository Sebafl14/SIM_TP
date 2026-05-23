import math
import num_generator as ng

class DistributionGen:
    def __init__(self, seed):
        self.last_u = None
        self.rng = ng.NumGenerator(seed)
        self.n2 = None
        self.n2_used = True

    def uniform(self, a=0.0, b=1.0):
        # Retorna (RND, Tiempo)
        u = float(self.rng.generate_random_number(True, True))
        self.last_u = u
        res = a + u * (b - a)
        return u, round(res, 4)

    def exponential(self, mu=None, lambd=None):
        if mu is None or mu == 0:
            mu = 1.0 / lambd
        if mu <= 0.0:
            raise ValueError("El valor enviado debe ser mayor a 0.0")

        u = self.rng.generate_random_number(True, False)
        self.last_u = u
        res = -mu * math.log(1.0 - u)
        return u, round(res, 4)
