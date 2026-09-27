# Sistema de Búsqueda Basado en Reglas — Red Ferroviaria de Colombia

Actividad de la clase de **Inteligencia Artificial** — Universidad Iberoamericana.

Sistema de **búsqueda y toma de decisiones** que, a partir de una base de conocimiento
escrita en reglas lógicas, encuentra la mejor ruta en **tren de pasajeros** para ir de
un **punto A** a un **punto B** sobre la red férrea **proyectada** para Colombia:
Corredor del Pacífico (Buenaventura – Cali – La Tebaida), conexión Pacífico–Central por
La Dorada y los trenes de cercanías de la Sabana de Bogotá (Regiotram de Occidente y del
Norte). El desplazamiento es 100% ferroviario: la red solo contiene rutas férreas
existentes o proyectadas (incluida una conexión **no oficial** La Tebaida – La Dorada
que da una alternativa cuando hay contingencias).
## Base de conocimiento

Cada tramo solo tiene **distancia** (km) y todas las vías están activas desde el inicio:

| Tramo | Distancia | Fuente |
|---|---|---|
| Buenaventura – Cali | 115 | Corredor del Pacífico (proyecto adjudicado) |
| Cali – La Tebaida | 175 | Ramal cafetero (proyecto adjudicado) |
| Cali – La Dorada | 310 | Conexión Pacífico–Central (PMTI, ANI) |
| La Tebaida – La Dorada | 170 | (Eje Cafetero – Río Magdalena) |
| La Dorada – Bogotá Centro | 185 | Corredor central |
| Bogotá Centro – Mosquera – Facatativá | 20 + 28 | Regiotram de Occidente |
| Bogotá Centro – Chía – Zipaquirá | 30 + 20 | Regiotram del Norte |

## Reglas lógicas

La velocidad de operación es estándar para toda la red: **50 km/h**.

| Regla | Lógica | Efecto |
|---|---|---|
| **R1 Clima** | SI está lloviendo ENTONCES la velocidad baja a 30 km/h | Cambia el tiempo estimado del viaje |
| **R2 Contingencia** | SI un tramo está cerrado ENTONCES el tren no puede usarlo: se busca otra ruta férrea más corta entre las disponibles | Si no existe alternativa férrea, **sugiere tomar un bus** en el tramo cerrado |

La ruta se encuentra con **búsqueda de costo uniforme (Dijkstra)** sobre la distancia:
las reglas filtran la red antes de buscar, y el sistema explica su decisión mostrando
qué reglas se activaron.

Además, el **escenario personalizado simula el azar del mundo real**: en cada
petición de ruta decide al azar **si llueve** (50% de probabilidad) y cierra al azar
**dos tramos** de la red (averías imprevistas), por lo que cada consulta enfrenta
condiciones operativas distintas.

## Cómo ejecutar

```bash
python sistema_ferroviario_reglas.py
```

Solo requiere Python 3. El menú trae los tres ejemplos de prueba y una opción de
**escenario personalizado** (el usuario elige el punto A y el punto B; el clima y dos
tramos cerrados se deciden al azar).

## Ejemplos de prueba

1. **Cali → Bogotá Centro, condiciones normales.**
   Ruta: `Cali → La Dorada → Bogotá Centro` (495 km, 594 min a 50 km/h). Es la más
   corta; la alternativa por La Tebaida mide 530 km.

2. **Cali → Bogotá Centro con lluvia (R1).**
   Misma ruta, pero la velocidad baja a 30 km/h y el tiempo sube a 990 min (16 h 30).

3. **Facatativá → Bogotá Centro con el tramo Mosquera – Bogotá cerrado (R2).**
   No queda ruta férrea (Facatativá solo se conecta por Mosquera), así que el sistema
   sugiere: tren Facatativá → Mosquera (28 km) y **bus** Mosquera → Bogotá (20 km).

*Caso adicional 1 (llamando directamente a la función):* si se cierra **Cali – La
Dorada**, sí existe una ruta férrea alternativa y el sistema la encuentra:
`Cali → La Tebaida → La Dorada → Bogotá Centro` (530 km), usando la conexión del Eje
Cafetero.