class Camion:
    def __init__(self, id_camion: int, tipo: str, hora_llegada: float):
        self.id = id_camion
        self.tipo = tipo  # "General" o "Perecedera"
        self.hora_llegada = hora_llegada
        self.estado = "EACD"  # Esperando Atencion Control Documental
        self.hora_inicio_espera_cd = hora_llegada
        self.hora_inicio_espera_rf = None
