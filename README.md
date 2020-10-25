# Covid 19 Spain Bot 

[![Build Status](https://github.com/aitormagan/covid19spainbot/workflows/Python%20package/badge.svg)](https://github.com//aitormagan/covid19spainbot/actions)
[![Coverage Status](https://coveralls.io/repos/github/aitormagan/covid19spainbot/badge.svg?branch=master)](https://coveralls.io/github/aitormagan/covid19spainbot?branch=master)

Script que publica en Twitter los nuevos PCR+ y fallecimientos provocados por el SARS-CoV-2 en España y disgregado por
las diferentes comunidades autónomas.

A diferencia de los datos del ministerio, que únicamente da las PCR+ que se ejecutaron y obtuvieron resultado el día 
anterior, este script comprueba la diferencia de datos entre el reporte del día actual y el anterior, para notificar el 
número total de nuevos positivos del día.

Links: 
* Bot: [https://twitter.com/CoronaSpainBot](https://twitter.com/CoronaSpainBot)
* Dashboard Evolución: [https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1](https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1)
* Dashboard Comparación: [https://home.aitormagan.es/d/h6K39NRRk/covid19-comparison?orgId=1](https://home.aitormagan.es/d/h6K39NRRk/covid19-comparison?orgId=1)

## Ejecución

El repositorio cuenta con dos scripts: 

* `main_daily`: debe lanzarse de lunes a viernes en intervalos de 5 minutos. Comprueba si se ha publicado el nuevo 
informe y en caso positivo actualiza la BBDD y publica los tweets.
* `main_weekly`: debe lanzarse una única vez los domingos para publicar las estadísticas semanales. 

Para planificar la ejecución de ambos scripts puedes hacer uso de `cron`. En concreto, estas son las expresiones que 
se están usando para cada uno de los scripts:

* `main_daily`: `*/5 16-21 * * 1-5` (cada 5 minutos de 16 a 21h de lunes a viernes)
* `main_weekly`: `0 18 * * 0` (los domingos a las 18.00h)

Ten en cuenta que deben definirse ciertas variables de entorno para lanzar los scripts:

* `API_SECRET`: Twitter API Secret (required)
* `API_SECRET_KEY`: Twitter API Secret Key (required)
* `ACCESS_TOKEN`: Twitter Access Token (required)
* `ACCESS_TOKEN_SECRET`: Twitter Access Token Secret (required)
* `INFLUX_HOST`: InfluxDB host (not required, default: `localhost`)
* `GRAFANA_SERVER`: Protocol + Host + Port where Grafana server is hosted (not required, default: 
`http://localhost:3000/`)

Para la ejecución por tanto, puedes crear unos scripts que defininan dichas variables y lancen los scripts. Por ejemplo:

```
export API_SECRET="<YOUR_API_SECRET>"
export API_SECRET_KEY="<YOUR_API_SECRET_KEY>"
export ACCESS_TOKEN="<YOUR_ACCESS_TOKEN>"
export ACCESS_TOKEN_SECRET="<YOUR_ACCESS_TOKEN_SECRET>"
export INFLUX_HOST="<INFLUX_HOST>"
export GRAFANA_SEVER="<GRAFANA_SERVER>"

python3 <PATH_TO_REPO_FOLDER>/main_daily.py     # Daily
python3 <PATH_TO_REPO_FOLDER>/main_weekly.py    # Weekly
```

## Tests

Puedes ejecutar los tests mediante la ejecución del siguiente comando:

```sh
$ tox
```

Si no tienes instalado `tox`, puedes instalarlo ejecutando:

```sh
$ pip3 install tox
```
