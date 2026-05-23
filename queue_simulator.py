from collections import deque
from cargas import Camion

class QueueSimulator:
    def __init__(self):
        # deque() es como una lista que permite sacar y agregar un elemento a la cola de forma instantanea sin importar el tamaño de la cola
        self.cola_general = deque()
        self.cola_perecedera = deque()
        self.cola_revision = deque()

    def agregar_control(self, camion: Camion):
        if camion.tipo == "Perecedera":
            self.cola_perecedera.append(camion)
        else:
            self.cola_general.append(camion)

    def tiene_camiones_control(self) -> bool:
        return len(self.cola_perecedera) > 0 or len(self.cola_general) > 0

    def desencolar_control(self) -> Camion:
        if len(self.cola_perecedera) > 0:
            return self.cola_perecedera.popleft()
        return self.cola_general.popleft()

    def agregar_revision(self, camion: Camion):
        camion.estado = "EARF"
        self.cola_revision.append(camion)

    def desencolar_revision(self) -> Camion:
        if len(self.cola_revision) > 0:
            return self.cola_revision.popleft()
        return None
