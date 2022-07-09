import random
from time import time
from copy import deepcopy
from pathlib import Path
from decimal import Decimal
from typing import List, Optional, Tuple
from concurrent.futures import Future, ThreadPoolExecutor

import click
import simplejson as json
import matplotlib.pyplot as plt

from logging_config import get_logger

log = get_logger(__name__)

HV = Decimal(9999999)
PLOTS_DIR = "plots"
PLOTS_PATH = Path(__file__).parent / PLOTS_DIR


def intervalo_entre_arribos(real_time: int) -> Decimal:
    if (real_time % 1440) < 360:
        # 0hs y las 6hs: Entre 0.6 y 1.2 segundos.
        return Decimal(random.uniform(0.01, 0.02))
    else:
        # Resto del dia: Entre 0.05 y 0.1 segundos.
        return Decimal(random.uniform(0.0008, 0.0016))


def generar_tiempo_atencion() -> Decimal:
    # Uniforme entre 3 y 4 segundos.
    return Decimal(random.uniform(0.05, 0.066))


def generar_demora() -> int:
    # Uniforme entre 10 y 30 minutos.
    return int(random.uniform(10, 30))


def requiere_escalado(pec: Decimal, umbral_escalado: int) -> bool:
    return pec >= Decimal(umbral_escalado)


def requiere_descalado(pto: Decimal, umbral_descalado: int) -> bool:
    return pto >= Decimal(umbral_descalado)


def indice_de_menor(lista: List[int]) -> int:
    min_value = min(lista)

    return lista.index(min_value)


def hv_en_tps(tps: List[Decimal]) -> int:
    return next(idx for idx, t_salida in enumerate(tps) if t_salida == HV)


def atender_peticiones(real_time: int, cant_serv: int) -> Decimal:
    ns = 0
    sta = 0
    cll = 0
    sps = 0
    tps = [HV] * cant_serv
    ito = [0] * cant_serv
    sto = [0] * cant_serv
    tpll = 0
    _time = 0
    tf = 1

    # Calcula la cantidad de peticiones que llegaron
    # en los pasados 1 minuto con un EaE.
    while _time < tf:
        menor_idx = indice_de_menor(tps)
        if tpll < tps[menor_idx]:
            # Llegada
            sps += (tpll - _time) * ns
            _time = deepcopy(tpll)
            ia = intervalo_entre_arribos(real_time)
            tpll = _time + ia
            ns += 1
            cll += 1
            if ns <= cant_serv:
                idx_puesto_libre = hv_en_tps(tps)
                ta = generar_tiempo_atencion()
                sta += ta
                tps[idx_puesto_libre] = _time + ta
                sto[idx_puesto_libre] = sto[idx_puesto_libre] + (
                    _time - ito[idx_puesto_libre]
                )
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
                tps[menor_idx] = deepcopy(HV)
                ito[menor_idx] = deepcopy(_time)

    pec = (sps - sta) / cll
    if pec < 0:
        pec = 0

    # for idx in range(len(sto)):
    #     # Si TPS == HV significa que nunca ejecuto nada.
    #     if ito[idx] == 0 and tps[idx] == HV:
    #         sto[idx] = tf

    sto_max = max(sto)
    pto_max = (sto_max * 100) / tf

    return Decimal(pec), Decimal(pto_max)


def run_model_from(
    thread_idx: int,
    tiempo_final: int,
    delta_t: int,
    cant_serv: int,
    costo_por_iniciar_serv: int,
    costo_por_min_serv: int,
    umbral_escalado: int,
    umbral_descalado: int,
) -> Tuple[int, Decimal, Decimal, Decimal]:
    _time = 0
    pec1 = 0  # Promedio de espera en cola mas alto
    pto1 = 0  # Porcentaje de tiempo ocioso mas alto
    ct = Decimal(0)
    fpe = 0  # Fecha de proximo escalado
    costo_inicio = 0

    # Guarda el estado de la simulacion para graficarlo
    # con el comando plot-results.
    STATE = []

    while _time < tiempo_final:
        _time = _time + delta_t

        if _time == fpe:
            cant_serv += 1
            costo_inicio = costo_por_iniciar_serv
            log.info(f"Thread - {thread_idx}: Escalando a {cant_serv} servidores")
        else:
            costo_inicio = 0

        pec, pto = atender_peticiones(_time, cant_serv)
        if pec > pec1:
            pec1 = pec

        if pto > pto1:
            pto1 = pto

        if fpe < _time and requiere_escalado(pec, umbral_escalado):
            fpe = _time + generar_demora()
        elif requiere_descalado(pto, umbral_descalado) and cant_serv > 1:
            cant_serv -= 1
            log.info(f"Thread - {thread_idx}: De-escalando a {cant_serv} servidores")

        ct += (cant_serv * costo_por_min_serv * delta_t) + costo_inicio
        STATE.append(f"{_time},{pec},{pto},{ct},{cant_serv}")

    PLOTS_PATH.mkdir(parents=True, exist_ok=True)
    with open(PLOTS_PATH / f"plot_{thread_idx}.txt", "w") as f:
        f.write("|".join(STATE))

    return umbral_escalado, umbral_descalado, pec1, pto1, ct, cant_serv


def post_process_analisis_de_sensibilidad(
    ctx, params, value: Optional[str]
) -> Optional[str]:
    ret_value = None
    if value:
        ret_value = value.split("|")
        ret_value = [v.split(",") for v in ret_value]

    return ret_value


@click.group(chain=True)
def model():
    pass


def print_results(results: List[dict]) -> None:
    """Prints and saves results.

    Args:
        results: List of smiulation results.
    """

    print("-" * 20)
    for vars in results:
        print(
            (
                "Umbral de escalado: {escalado}\nUmbral de de-escalado: {descalado}%\n"
                "Cantidad final de servidores: {cant_serv_final},Promedio de espera en cola mas alto: {pec1}, "
                "Porcentaje de tiempo ocioso mas alto: {pto1}, Costo Total: {costo_total}"
            ).format(**vars)
        )
        print("-" * 20)

    with open("./results/latest-run.json", "w") as f:
        json.dump(results, f, indent=2)


@model.command()
@click.option(
    "-e",
    "--escalado",
    type=Decimal,
    default=Decimal(0.05),  # Valor en minutos.
    show_default=True,
    help="Espera en cola maximo para escalar.",
)
@click.option(
    "-d",
    "--descalado",
    type=int,
    default=20,  # 20%
    show_default=True,
    help="Porcentaje de tiempo ocioso para de-escalar.",
)
@click.option(
    "-tf", "--tiempo-final", type=int, default=43200, show_default=True  # 1 mes
)
@click.option(
    "-cs",
    "--cant-serv-base",
    type=int,
    default=2,
    show_default=True,
    help="Cantidad de servidores inicial.",
)
@click.option(
    "-as",
    "--analisis-sensibilidad",
    type=str,
    show_default=True,
    callback=post_process_analisis_de_sensibilidad,
    help="Valores de umbral de escalado, de-escalado y cantidad de servidores"
    " para analisis de sensibilidad separados por comas entre ellos"
    " y por pipes entre distintos analisis. Ejemplo: 0.1,0.2,4|0.5,1,6",
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
    escalado: Optional[Decimal] = 0.05,
    descalado: Optional[int] = 20,
    cant_serv_base: Optional[int] = 5,
    analisis_sensibilidad: Optional[List[str]] = None,
    max_threads: Optional[int] = 3,
):
    delta_t: int = 1  # minutos
    costo_por_min_serv: int = 20  # Averiguar el costo x minuto real.
    costo_por_iniciar_serv: int = 2000  # Costo de iniciar un servidor
    analisis_sensibilidad = analisis_sensibilidad or [
        (escalado, descalado, cant_serv_base)
    ]

    start = time()
    results: List[dict] = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures: List[Future] = []
        for idx, (escalado, descalado, cant_serv) in enumerate(analisis_sensibilidad):
            futures.append(
                executor.submit(
                    run_model_from,
                    idx,
                    tiempo_final,
                    delta_t,
                    int(cant_serv),
                    costo_por_iniciar_serv,
                    costo_por_min_serv,
                    float(escalado),
                    int(descalado),
                )
            )
        for future in futures:
            (escalado, descalado, pec1, pto1, ct, cant_serv) = future.result()

            results.append(
                {
                    "escalado": escalado,
                    "descalado": descalado,
                    "cant_serv_final": cant_serv,
                    "pec1": pec1,
                    "pto1": pto1,
                    "costo_total": ct,
                }
            )

    end = time()

    print_results(results)

    print(f"Tiempo total de ejecucion: {end - start}")


@model.command()
@click.option(
    "-f",
    "--file-numbers",
    type=str,
    default="1",
    help="Numeros de archivo para graficar separados por coma. Ejemplos: 1 o 0,1",
    show_default=True,
)
def plot_results(file_numbers: Optional[str] = "1"):
    for file_number in map(int, file_numbers.split(",")):
        names = {
            "PEC": (0, 0),
            "PTO": (0, 1),
            "Costo Total": (1, 0),
            "Cantidad de servidores": (1, 1),
        }
        x = [[], [], [], []]
        y = [[], [], [], []]

        _, axs = plt.subplots(2, 2)
        with open(PLOTS_PATH / f"plot_{file_number}.txt", "r") as f:
            lines = f.read()
            lines = [l for l in lines.split("|")]

        for line in lines:
            _time = line.split(",")[0]
            for value in x:
                value.append(int(_time))
            for idx, val in enumerate(line.split(",")[1:]):
                y[idx].append(float(val))

        for idx, (name, (axis_x, axis_y)) in enumerate(names.items()):
            axs[axis_x, axis_y].set_title(name)

        for idx, (name, (axis_x, axis_y)) in enumerate(names.items()):
            x_vals = x[idx]
            y_vals = y[idx]

            axs[axis_x, axis_y].plot(x_vals, y_vals)

    plt.show()


if __name__ == "__main__":
    model()
