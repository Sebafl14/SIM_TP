from events import Evento
from distribution_generator import DistributionGen
from control import ServidorControl, ServidorRevision
from queue_simulator import QueueSimulator
from cargas import Camion

class SimulationEngine:
    def __init__(self, semilla: int, media_gen: float, media_per: float,
                 cd_min: float, cd_max: float, rf_min: float, rf_max: float, prob_rf: float):

        self.dist_gen = DistributionGen(seed=semilla)

        self.media_gen = media_gen
        self.media_per = media_per
        self.cd_min = cd_min
        self.cd_max = cd_max
        self.rf_min = rf_min
        self.rf_max = rf_max
        self.prob_rf = prob_rf  # Probabilidad de revisión física parametrizada desde la UI

        self.controles = [ServidorControl(1), ServidorControl(2), ServidorControl(3)]
        self.revision = ServidorRevision()
        self.colas = QueueSimulator()

        self.prox_llegada_gen = 0.0
        self.prox_llegada_per = 0.0

        self.camiones_activos: dict[int, Camion] = {}
        self.contador_camiones = 0

        self.acum_espera_gen = 0.0
        self.cant_ingresos_gen = 0
        self.acum_espera_per = 0.0
        self.cant_ingresos_per = 0

        self.tiempo_acum_utilizacion_rf = 0.0
        self.ultimo_cambio_rf = 0.0
        self.max_camiones_recinto = 0

    def inicializar_sistema(self) -> dict:
        rnd_g, t_g = self.dist_gen.exponential(mu=self.media_gen)
        rnd_p, t_p = self.dist_gen.exponential(mu=self.media_per)

        self.prox_llegada_gen = t_g
        self.prox_llegada_per = t_p

        return self._crear_fila_estado(0.0, Evento.INICIALIZACION, rnd_g, t_g, rnd_p, t_p)

    def simular_paso(self, reloj_actual: float, evento_actual: str) -> dict:
        if self.revision.estado == "Ocupado":
            self.tiempo_acum_utilizacion_rf += (reloj_actual - self.ultimo_cambio_rf)
        self.ultimo_cambio_rf = reloj_actual

        rnd_llegada_gen, t_llegada_gen = "-", "-"
        rnd_llegada_per, t_llegada_per = "-", "-"
        rnd_rf, t_rf = "-", "-"

        rnd_cd = {"1": "-", "2": "-", "3": "-"}
        t_cd = {"1": "-", "2": "-", "3": "-"}

        rnd_inspeccion = "-"
        pasa_inspeccion = "-"

        if evento_actual == Evento.LLEGADA_GENERAL:
            self.contador_camiones += 1
            nuevo_camion = Camion(self.contador_camiones, "General", reloj_actual)
            self.camiones_activos[nuevo_camion.id] = nuevo_camion

            rnd_llegada_gen, t_llegada_gen = self.dist_gen.exponential(mu=self.media_gen)
            self.prox_llegada_gen = round(reloj_actual + t_llegada_gen, 4)

            puesto_libre = next((c for c in self.controles if c.estado == "Libre"), None)
            if puesto_libre and not self.colas.tiene_camiones_control():
                p_id = str(puesto_libre.id)
                u, t = self.dist_gen.uniform(self.cd_min, self.cd_max)
                rnd_cd[p_id], t_cd[p_id] = u, t
                puesto_libre.ocupar(nuevo_camion, round(reloj_actual + t, 4))
                self.cant_ingresos_gen += 1
            else:
                self.colas.agregar_control(nuevo_camion)

        elif evento_actual == Evento.LLEGADA_PERECEDERA:
            self.contador_camiones += 1
            nuevo_camion = Camion(self.contador_camiones, "Perecedera", reloj_actual)
            self.camiones_activos[nuevo_camion.id] = nuevo_camion

            rnd_llegada_per, t_llegada_per = self.dist_gen.exponential(mu=self.media_per)
            self.prox_llegada_per = round(reloj_actual + t_llegada_per, 4)

            puesto_libre = next((c for c in self.controles if c.estado == "Libre"), None)
            if puesto_libre and not self.colas.tiene_camiones_control():
                p_id = str(puesto_libre.id)
                u, t = self.dist_gen.uniform(self.cd_min, self.cd_max)
                rnd_cd[p_id], t_cd[p_id] = u, t
                puesto_libre.ocupar(nuevo_camion, round(reloj_actual + t, 4))
                self.cant_ingresos_per += 1
            else:
                self.colas.agregar_control(nuevo_camion)

        elif evento_actual in [Evento.FIN_CONTROL_1, Evento.FIN_CONTROL_2, Evento.FIN_CONTROL_3]:
            id_puesto_str = evento_actual[-1]
            idx = int(id_puesto_str) - 1
            puesto = self.controles[idx]
            camion_saliente = puesto.camion_actual

            puesto.liberar()

            rnd_inspeccion = self.dist_gen.rng.generate_random_number(True, True)
            if rnd_inspeccion < self.prob_rf:
                pasa_inspeccion = "Si"
                camion_saliente.hora_inicio_espera_rf = reloj_actual
                if self.revision.estado == "Libre":
                    rnd_rf, t_rf = self.dist_gen.uniform(self.rf_min, self.rf_max)
                    self.revision.ocupar(camion_saliente, round(reloj_actual + t_rf, 4))
                else:
                    self.colas.agregar_revision(camion_saliente)
            else:
                pasa_inspeccion = "No"
                camion_saliente.estado = "FR"
                if camion_saliente.id in self.camiones_activos:
                    del self.camiones_activos[camion_saliente.id]

            if self.colas.tiene_camiones_control():
                proximo_camion = self.colas.desencolar_control()
                u, t = self.dist_gen.uniform(self.cd_min, self.cd_max)
                rnd_cd[id_puesto_str], t_cd[id_puesto_str] = u, t
                puesto.ocupar(proximo_camion, round(reloj_actual + t, 4))

                espera = round(reloj_actual - proximo_camion.hora_inicio_espera_cd, 4)
                if proximo_camion.tipo == "General":
                    self.acum_espera_gen += espera
                    self.cant_ingresos_gen += 1
                else:
                    self.acum_espera_per += espera
                    self.cant_ingresos_per += 1

        elif evento_actual == Evento.FIN_REVISION:
            camion_saliente = self.revision.camion_actual
            self.revision.liberar()
            camion_saliente.estado = "FR"
            if camion_saliente.id in self.camiones_activos:
                del self.camiones_activos[camion_saliente.id]

            if len(self.colas.cola_revision) > 0:
                proximo_camion = self.colas.desencolar_revision()
                rnd_rf, t_rf = self.dist_gen.uniform(self.rf_min, self.rf_max)
                self.revision.ocupar(proximo_camion, round(reloj_actual + t_rf, 4))

        camiones_en_recinto = len(self.camiones_activos)
        if camiones_en_recinto > self.max_camiones_recinto:
            self.max_camiones_recinto = camiones_en_recinto

        return self._crear_fila_estado(reloj_actual, evento_actual, rnd_llegada_gen, t_llegada_gen,
                                      rnd_llegada_per, t_llegada_per, rnd_cd=rnd_cd, t_cd=t_cd,
                                      rnd_inspeccion=rnd_inspeccion, pasa_inspeccion=pasa_inspeccion,
                                      rnd_rf=rnd_rf, t_rf=t_rf)

    def evento_fin_simulacion(self, reloj_final: float) -> dict:
        """ Método especial para procesar las métricas pendientes al instante exacto X """
        if self.revision.estado == "Ocupado":
            self.tiempo_acum_utilizacion_rf += (reloj_final - self.ultimo_cambio_rf)
        self.ultimo_cambio_rf = reloj_final

        # Sumamos las esperas acumuladas parciales de los camiones estancados en las colas
        for camion in self.colas.cola_general:
            espera_parcial = round(reloj_final - camion.hora_inicio_espera_cd, 4)
            self.acum_espera_gen += espera_parcial
            self.cant_ingresos_gen += 1

        for camion in self.colas.cola_perecedera:
            espera_parcial = round(reloj_final - camion.hora_inicio_espera_cd, 4)
            self.acum_espera_per += espera_parcial
            self.cant_ingresos_per += 1

        return self._crear_fila_estado(reloj_final, "Fin_Simulacion")

    def _crear_fila_estado(self, reloj, evento, rnd_lg="-", t_lg="-", rnd_lp="-", t_lp="-",
                            rnd_cd=None, t_cd=None, rnd_inspeccion="-", pasa_inspeccion="-",
                            rnd_rf="-", t_rf="-") -> dict:

        if rnd_cd is None:
            rnd_cd = {"1": "-", "2": "-", "3": "-"}
        if t_cd is None:
            t_cd = {"1": "-", "2": "-", "3": "-"}

        prom_gen = round(self.acum_espera_gen / self.cant_ingresos_gen, 4) if self.cant_ingresos_gen > 0 else 0.0
        prom_per = round(self.acum_espera_per / self.cant_ingresos_per, 4) if self.cant_ingresos_per > 0 else 0.0
        porcentaje_rf = round((self.tiempo_acum_utilizacion_rf / reloj) * 100, 2) if reloj > 0 else 0.0

        fila = {
            "Reloj": reloj,
            "Evento": evento,
            "RND Llegada Carga General": rnd_lg,
            "Tiempo entre Llegadas Carga General": t_lg,
            "Proxima Llegada General": self.prox_llegada_gen,
            "RND Llegada Carga Perecedera": rnd_lp,
            "Tiempo entre Llegadas Carga Perecedera": t_lp,
            "Proxima Llegada Perecedera": self.prox_llegada_per,
            "Cola Documental General": len(self.colas.cola_general),
            "Cola Documental Perecedera": len(self.colas.cola_perecedera),

            "Estado Control 1": self.controles[0].estado,
            "RND Fin Control 1": rnd_cd["1"],
            "Tiempo Fin Control 1": t_cd["1"],
            "Fin Control 1": self.controles[0].fin_atencion if self.controles[0].fin_atencion else "-",

            "Estado Control 2": self.controles[1].estado,
            "RND Fin Control 2": rnd_cd["2"],
            "Tiempo Fin Control 2": t_cd["2"],
            "Fin Control 2": self.controles[1].fin_atencion if self.controles[1].fin_atencion else "-",

            "Estado Control 3": self.controles[2].estado,
            "RND Fin Control 3": rnd_cd["3"],
            "Tiempo Fin Control 3": t_cd["3"],
            "Fin Control 3": self.controles[2].fin_atencion if self.controles[2].fin_atencion else "-",

            "RND Inspeccion Profunda": rnd_inspeccion,
            "¿Pasa a revision fisica?": pasa_inspeccion,

            "Cola Revision Fisica": len(self.colas.cola_revision),
            "Estado Revision": self.revision.estado,
            "RND Ocupacion Revision": rnd_rf,
            "Tiempo Ocupacion Revision": t_rf,
            "Fin Revision": self.revision.fin_atencion if self.revision.fin_atencion else "-",

            "AC Espera Carga General": self.acum_espera_gen,
            "Promedio Espera General": prom_gen,
            "AC Espera Carga Perecedera": self.acum_espera_per,
            "Promedio Espera Perecedera": prom_per,
            "Tiempo Acumulado Revision": self.tiempo_acum_utilizacion_rf,
            "Porcentaje Utilizacion Revision": porcentaje_rf,
            "Camiones en Recinto": len(self.camiones_activos),
            "Maximo Camiones": self.max_camiones_recinto
        }

        # SOLUCIÓN DEFINITIVA: Mapeo dinámico escalable al máximo histórico real
        camiones_vivos = sorted(self.camiones_activos.values(), key=lambda x: x.id)

        # Iteramos dinámicamente hasta la cantidad máxima de camiones que hayan coexistido en el recinto
        tope_columnas = self.max_camiones_recinto if self.max_camiones_recinto > 0 else 1

        for i in range(1, tope_columnas + 1):
            if i <= len(camiones_vivos):
                c = camiones_vivos[i-1]
                fila[f"Camion Pos {i} ID"] = c.id
                fila[f"Camion Pos {i} Tipo"] = c.tipo
                fila[f"Camion Pos {i} Estado"] = c.estado
            else:
                fila[f"Camion Pos {i} ID"] = "-"
                fila[f"Camion Pos {i} Tipo"] = "-"
                fila[f"Camion Pos {i} Estado"] = "-"

        return fila
