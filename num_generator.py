import random

class NumGenerator:
    def __init__(self, seed=None, a=1664525, c=1013904223, m=2 ** 32): # los valores son un estandar para asegurar que pasa por los 2^32 nros antes de repetirse(tienen un periodo completo)
        if seed is None:
            seed = random.randrange(m)
        self.a = a % m # Al colocar el % m estamos normalizando cualquier entrada
        self.c = c % m
        self.m = m
        self.state = seed % m
        self.last_x = self.state

    def _generate_next(self):
        # Formula del metodo congruencial mixto
        self.state = (self.c + self.a * self.state) % self.m
        return self.state

    def generate_random_number(self, inf_cerrado, sup_cerrado):
        x = self._generate_next()
        self.last_x = x
        """
        Genera un número aleatorio con el método de Congruencia
        :param inf_cerrado: Booleano para incluir el 0 o no.
        :param sup_cerrado: Booleano para incluir el 1 o no.
        :return: Devuelve un número aleatorio entre 0 y 1
        """
        if inf_cerrado:
            if not sup_cerrado:
                return x / self.m
            return x / (self.m - 1)
        return (x + 0.5) / self.m
