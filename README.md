# Covid 19 Spain Bot

Este script publica tweets con el número de nuevas PCR+ de SARS-CoV-2 en España agrupados por comunidad autónoma. 

Esta información es pública y hay muchas páginas donde puede verse. Sin embargo, debido a la complejidad con la que la Comunidad de Madrid publica los datos (actualizando la serie histórica), parece que el número de casos en dicha comunidad son menos de los reales. La intención de este bot es precisamente esa: tener el dato real de incremento de casos de la misma forma que se tiene para el resto de comunidades autónomas.

El funcionamiento es sencillo:

1. Se baja el fichero de la web del Instituto de Salud Carlos III
2. Comprueba si el fichero está actualizado
3. Si lo está, compara los datos con el día anterior
4. Publica los tweets (con un límite de 240 caracteres)
