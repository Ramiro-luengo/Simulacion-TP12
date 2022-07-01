# Simulacion-TP12


## Instrucciones para correr el modelo

1. Crear un virtualenv con el siguiente comando: 
```bash
python -m venv ./venv
```
2. Activar el virtualenv.
3. Instalar poetry dentro del venv con el siguiente comando: 
```bash
pip install poetry
```
4. Correr poetry install para instalar las dependencias requeridas.
5. Correr:
```bash
>>> python model.py --help

  -u, --umbral-escalado INTEGER   Espera en cola maximo para escalar.
                                  [default: 1]
  -tf, --tiempo-final INTEGER     [default: 43200]
  -cs, --cant-serv INTEGER        Cantidad de servidores inicial.  [default:  
                                  5]
  -as, --analisis-sensibilidad TEXT
                                  Valores de umbral de escalado para analisis 
                                  de sensibilidad separados por coma. Ejemplo:
                                  0.1,0.2,0.5,1
  -mt, --max-threads INTEGER      [default: 3]
  --help                          Show this message and exit.
``` 
