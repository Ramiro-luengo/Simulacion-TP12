import math
import random
from time import time
from copy import deepcopy
from decimal import Decimal
from typing import List, Optional, Tuple
from concurrent.futures import Future, ThreadPoolExecutor

import click


def generar_tiempo_atencion() -> Decimal:
    # Uniforme entre 1 y 3 segundos.
    return Decimal(random.uniform(0.016, 0.05))


def generar_demora() -> int:
    # Uniforme entre 10 y 30 minutos.
    return int(random.uniform(10, 30))


def requiere_escalado(pec: Decimal, umbral_escalado: int) -> bool:
    return pec > Decimal(umbral_escalado)


def intervalo_entre_arribos() -> Decimal:
    # Entre 10 y 20 segundos con el doble probabilidad que sea 20 que 10.
    # r = random.random()
    # func = math.sqrt(300*r + 10) / 60 # Divido por 60 para llevarlo a minutos.
    # return Decimal(func)

    return Decimal(0.01)


def indice_de_menor(lista: List[int]) -> int:
    min_value = min(lista)

    return lista.index(min_value)


def hv_en_tps(hv: Decimal, tps: List[Decimal]) -> int:
    return next(idx for idx, t_salida in enumerate(tps) if t_salida == hv)


def atender_peticiones(cant_serv: int) -> Decimal:
    hv = Decimal(9999999)
    ns = 0
    sta = 0
    cll = 0
    sps = 0
    tps = [hv] * cant_serv
    tpll = 0
    _time = 0

    # Calcula la cantidad de peticiones que llegaron
    # en los pasados 10 minutos con un EaE.
    while _time < 10:
        menor_idx = indice_de_menor(tps)
        if tpll < tps[menor_idx]:
            # Llegada
            sps += (tpll - _time) * ns
            _time = deepcopy(tpll)
            ia = intervalo_entre_arribos()
            tpll = _time + ia
            ns += 1
            cll += 1
            if ns <= cant_serv:
                idx_puesto_libre = hv_en_tps(hv, tps)
                ta = generar_tiempo_atencion()
                sta += ta
                tps[idx_puesto_libre] = _time + ta
        else:
            # Salida
            sps = (tps[menor_idx] - _time) * ns
            _time = deepcopy(tps[menor_idx])
            ns -= 1
            if ns >= cant_serv:
                ta = generar_tiempo_atencion()
                sta += ta
                tps[menor_idx] = _time + ta
            else:
                tps[menor_idx] = deepcopy(hv)

    pec = (sps - sta) / cll

    return Decimal(pec)


def run_model_from(
    tiempo_final: int,
    delta_t: int,
    cant_serv: int,
    costo_por_iniciar_serv: int,
    costo_por_min_serv: int,
    umbral_escalado: int,
) -> Tuple[int, Decimal, Decimal]:
    _time: int = 0
    pec1: int = 0  # Promedio de espera en cola mas alto en 1 mes
    ct: Decimal = Decimal(0)
    fpe: int = 0  # Fecha de proximo escalado
    costo_inicio: int = 0

    while _time < tiempo_final:
        _time = _time + delta_t

        if _time == fpe:
            cant_serv += 1
            costo_inicio = costo_por_iniciar_serv
        else:
            costo_inicio = 0

        pec = atender_peticiones(cant_serv)
        if pec > pec1:
            pec1 = pec

        if fpe < _time and requiere_escalado(pec, umbral_escalado):
            fpe = _time + generar_demora()

        ct += (cant_serv * costo_por_min_serv * delta_t) + costo_inicio

    return umbral_escalado, pec1, ct


@click.command()
@click.option(
    "-u",
    "--umbral-escalado",
    type=int,
    default=1,
    show_default=True,
    help="Espera en cola maximo para escalar.",
)
@click.option(
    "-tf", "--tiempo-final", type=int, default=43200, show_default=True
)  # 1 mes
@click.option(
    "-cs",
    "--cant-serv",
    type=int,
    default=5,
    show_default=True,
    help="Cantidad de servidores inicial.",
)
@click.option(
    "-as",
    "--analisis-sensibilidad",
    type=str,
    show_default=True,
    help="Valores de umbral de escalado para analisis de sensibilidad separados por coma. Ejemplo: 0.1,0.2,0.5,1",
)
@click.option(
    "-mt",
    "--max-threads",
    type=int,
    default=3,
    show_default=True,
)
def run_model(
    tiempo_final: Optional[int] = 43200,
    umbral_escalado: Optional[int] = 1,
    cant_serv: Optional[int] = 5,
    analisis_sensibilidad: Optional[str] = None,
    max_threads: Optional[int] = 3,
):
    delta_t: int = 10  # minutos
    costo_por_min_serv: int = 20  # Averiguar el costo x minuto real.
    costo_por_iniciar_serv: int = 2000  # Costo de iniciar un servidor
    analisis_sensibilidad = analisis_sensibilidad or [umbral_escalado]

    start = time()
    results = {}
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures: List[Future] = []
        for umbral in analisis_sensibilidad:
            futures.append(
                executor.submit(
                    run_model_from,
                    tiempo_final,
                    delta_t,
                    cant_serv,
                    costo_por_iniciar_serv,
                    costo_por_min_serv,
                    umbral,
                )
            )
        for future in futures:
            (umbral, pec1, ct) = future.result()
            results[
                umbral
            ] = f"Promedio de espera en cola mas alto: {pec1}, Costo Total: {ct}"

    end = time()
    for umbral, result_str in results.items():
        print(f"Umbral de escalado: {umbral}", result_str)

    print(f"Tiempo total de ejecucion: {end - start}")


if __name__ == "__main__":
    run_model()
