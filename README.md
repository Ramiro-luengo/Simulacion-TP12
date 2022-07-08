# Simulacion-TP12


## Instrucciones para correr el modelo

1. Crear un virtualenv con el siguiente comando: 
```bash
$ python -m venv ./venv
```
2. Activar el virtualenv.
3. Instalar poetry dentro del venv con el siguiente comando: 
```bash
$ pip install poetry
```
4. Instalar las dependencias requeridas con el siguiente comando:
```bash
$ poetry install

# Y si no les reconoce el comando poetry pueden intentar con:
$ python -m poetry install

```

5. Correr:
```bash
$ python model.py run-model --help

  -e, --escalado DECIMAL          Espera en cola maximo para escalar.
                                  [default: 0.05000000000000000277555756156289
                                  135105907917022705078125]
  -d, --descalado INTEGER         Porcentaje de tiempo ocioso para de-escalar.
                                  [default: 20]
  -tf, --tiempo-final INTEGER     [default: 43200]
  -cs, --cant-serv-base INTEGER   Cantidad de servidores inicial.  [default:2]
  -as, --analisis-sensibilidad TEXT
                                  Valores de umbral de escalado, de-escalado y
                                  cantidad de servidores para analisis de
                                  sensibilidad separados por comas entre ellos
                                  y por pipes entre distintos analisis.
                                  Ejemplo: 0.1,0.2,4|0.5,1,6
  -mt, --max-threads INTEGER      [default: 3]
  --help
``` 

6. Graficar resultados:
```bash

$ python model.py plot-results

```
