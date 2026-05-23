from typing import Optional
from cargas import Camion

class ServidorControl:
    def __init__(self, id_servidor: int):
        self.id = id_servidor
        self.estado = "Libre"
        self.camion_actual: Optional[Camion] = None
        self.fin_atencion: Optional[float] = None

    def ocupar(self, camion: Camion, fin_atencion: float):
        self.estado = "Ocupado"
        self.camion_actual = camion
        self.fin_atencion = fin_atencion
        camion.estado = f"SACD({self.id})"

    def liberar(self):
        self.estado = "Libre"
        self.camion_actual = None
        self.fin_atencion = None


class ServidorRevision:
    def __init__(self):
        self.estado = "Libre"
        self.camion_actual: Optional[Camion] = None
        self.fin_atencion: Optional[float] = None

    def ocupar(self, camion: Camion, fin_atencion: float):
        self.estado = "Ocupado"
        self.camion_actual = camion
        self.fin_atencion = fin_atencion
        camion.estado = "SARF"

    def liberar(self):
        self.estado = "Libre"
        self.camion_actual = None
        self.fin_atencion = None
