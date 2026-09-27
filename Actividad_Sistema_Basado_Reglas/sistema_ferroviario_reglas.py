# -*- coding: utf-8 -*-
"""
==============================================================================
 SISTEMA INTELIGENTE BASADO EN REGLAS Red Ferroviaria de Colombia
==============================================================================
  ¿QUÉ HACE ESTE PROGRAMA?
   Busca la mejor ruta en tren para ir de un punto A a un punto B sobre la
   red férrea proyectada para Colombia, aplicando dos reglas de conocimiento:
     R1 Clima: si llueve, la velocidad de operación baja a 30 km/h.
     R2 Contingencia: si un tramo está cerrado, se busca otra ruta férrea;
        si no existe, se sugiere tomar un BUS en el tramo cerrado.
   Además, el escenario personalizado simula el azar del mundo real en
   cada petición de ruta: decide al azar si llueve y cierra dos tramos
   de la red por contingencia.
==============================================================================
"""

import heapq  # Cola de prioridad usada por la búsqueda de la ruta óptima
import random  # Se usa para cerrar tramos al azar (contingencias aleatorias)

# Velocidad de operación de los trenes (km/h) según el clima.
VELOCIDAD_NORMAL = 50
VELOCIDAD_LLUVIA = 30

# ============================================================================
# 1. BASE DE CONOCIMIENTO: LA RED FERROVIARIA
# ============================================================================
# Cada TRAMO es una conexión directa entre dos estaciones y SOLO tiene la
# distancia en kilómetros. Todas las vías están activas desde el inicio.

TRAMOS = [
    # Corredor del Pacífico
    {"origen": "Buenaventura", "destino": "Cali", "distancia_km": 115},
    {"origen": "Cali", "destino": "La Tebaida", "distancia_km": 175},

    # Conexión Pacífico - Central
    {"origen": "Cali", "destino": "La Dorada", "distancia_km": 310},

    # Conexión férrea Eje Cafetero - Río Magdalena.
    {"origen": "La Tebaida", "destino": "La Dorada", "distancia_km": 170},

    # Corredor central hasta Bogotá
    {"origen": "La Dorada", "destino": "Bogotá Centro", "distancia_km": 185},

    # Regiotram de Occidente
    {"origen": "Bogotá Centro", "destino": "Mosquera", "distancia_km": 20},
    {"origen": "Mosquera", "destino": "Facatativá", "distancia_km": 28},

    # Regiotram del Norte
    {"origen": "Bogotá Centro", "destino": "Chía", "distancia_km": 30},
    {"origen": "Chía", "destino": "Zipaquirá", "distancia_km": 20},
]

# Estaciones de la red (nodos del grafo).
ESTACIONES = [
    "Buenaventura", "Cali", "La Tebaida", "La Dorada", "Bogotá Centro",
    "Mosquera", "Facatativá", "Chía", "Zipaquirá",
]


# ============================================================================
# 2. MEMORIA DE TRABAJO: EL CONTEXTO DEL VIAJE
# ============================================================================
def crear_contexto(lluvia=False, tramos_bloqueados=None):
    """
    Crea el contexto del viaje con las dos únicas variables del sistema.

    Parámetros:
        lluvia            : True si está lloviendo (activa la regla R1).
        tramos_bloqueados : lista de pares (estación_a, estación_b) cuyas vías
                            están cerradas por contingencia (activa la regla R2).
    """
    return {"lluvia": lluvia, "tramos_bloqueados": tramos_bloqueados or []}


def generar_lluvia_aleatoria():
    """
    Decide al AZAR si está lloviendo en el momento de la petición de ruta
    Si devuelve True, la regla R1 baja la velocidad de los trenes a 30 km/h.
    """
    return random.choice([True, False])


def generar_contingencias_aleatorias(cantidad=2):
    """
    Cierra al AZAR 'cantidad' tramos de la red para simular averías o
    eventos imprevistos en la vía

    random.sample elige sin repetir, así que el mismo tramo nunca queda
    cerrado dos veces.
    """
    elegidos = random.sample(TRAMOS, cantidad)
    return [(tramo["origen"], tramo["destino"]) for tramo in elegidos]


# ============================================================================
# 3. BASE DE REGLAS
# ============================================================================
def regla_r1_clima(contexto):
    """
    R1 - CLIMA:
        SI  está lloviendo
        ENTONCES  la velocidad de operación de los trenes baja a 30 km/h.
    """
    if contexto["lluvia"]:
        return VELOCIDAD_LLUVIA
    return VELOCIDAD_NORMAL


def regla_r2_contingencia(tramo, contexto):
    """
    R2 - CONTINGENCIA DE VÍA:
        SI  el tramo está cerrado por contingencia
        ENTONCES  el tren NO puede operarlo: se busca otra ruta férrea y,
        si no existe, se sugiere tomar un BUS en ese tramo.
    """
    par = frozenset((tramo["origen"], tramo["destino"]))
    cerrados = [frozenset(par_bloqueado)
                for par_bloqueado in contexto["tramos_bloqueados"]]
    return par not in cerrados


# ============================================================================
# 4. MOTOR DE BÚSQUEDA: RUTA MÁS CORTA POR DISTANCIA (DIJKSTRA)
# ============================================================================
def construir_red(tramos):
    """Convierte la lista de tramos en un grafo de adyacencia bidireccional:
    {estación: [(vecino, tramo), ...]}."""
    red = {estacion: [] for estacion in ESTACIONES}
    for tramo in tramos:
        red[tramo["origen"]].append((tramo["destino"], tramo))
        red[tramo["destino"]].append((tramo["origen"], tramo))
    return red


def buscar_ruta_optima(origen, destino, red):
    """
    Búsqueda de costo uniforme que encuentra la ruta de MENOR
    DISTANCIA entre el origen y el destino.

    IDEA CENTRAL (dos diccionarios que trabajan juntos):
      - `distancia`: la mejor distancia conocida hasta cada estación.
      - `anterior` : para cada estación, desde cuál se llegó a ella con esa
                     mejor distancia (como migas de pan que va dejando la
                     búsqueda). Al final, seguir esas migas desde el destino
                     hacia el origen revela la ruta óptima.

    El `while` de abajo es la búsqueda en sí: explora el grafo y va dejando
    las migas de pan. La parte final solo camina hacia atrás siguiéndolas
    para escribir la ruta en orden.

    Devuelve un diccionario con la ruta y la distancia total, o None si no
    hay forma de llegar en tren.
    """
    # Cola de prioridad con las estaciones pendientes por explorar.
    # Siempre entrega primero la de MENOR distancia acumulada (esa es la
    # clave del método: siempre se expande la estación más cercana).
    cola = [(0, origen)]
    distancia = {origen: 0}             # mejor distancia conocida a cada estación
    anterior = {origen: (None, None)}   # migas de pan: estación -> (previa, tramo)

    # ================= BÚSQUEDA =================
    # Se repite mientras queden estaciones por explorar en la cola.
    while cola:
        # 1) Se saca de la cola la estación MÁS CERCANA al origen entre las
        #    que aún no se han explorado (heappop ordena por distancia).
        dist_actual, estacion = heapq.heappop(cola)

        # 2) Si la estación sacada ya es el destino, la búsqueda termina:
        #    como era la más cercana de la cola, ninguna ruta pendiente
        #    por explorar puede ser mejor que la ya encontrada.
        if estacion == destino:
            break

        # 3) Filtro de entradas viejas: una misma estación puede estar
        #    varias veces en la cola (se agregó cada vez que mejoró su
        #    distancia). Si la entrada recién sacada tiene una distancia
        #    PEOR que la mejor ya registrada, es una copia obsoleta y se
        #    descarta sin expandir nada.
        if dist_actual > distancia.get(estacion, float("inf")):
            continue

        # 4) RELAJACIÓN de arcos: por cada vecino de la estación actual se
        #    pregunta "¿llegar hasta él pasando por aquí mejora su mejor
        #    distancia conocida?". Si la mejora:
        #      - se actualiza su mejor distancia,
        #      - se deja la miga de pan (a este vecino se llegó desde la
        #        estación actual, usando este tramo),
        #      - y entra a la cola para explorarse más adelante.
        for vecino, tramo in red[estacion]:
            nueva_distancia = dist_actual + tramo["distancia_km"]
            if nueva_distancia < distancia.get(vecino, float("inf")):
                distancia[vecino] = nueva_distancia
                anterior[vecino] = (estacion, tramo)  # se deja la miga de pan
                heapq.heappush(cola, (nueva_distancia, vecino))

    # Si el destino nunca fue alcanzado, no existe ruta férrea posible.
    if destino not in distancia:
        return None

    # ============ RECONSTRUCCIÓN DE LA RUTA ============
    # La búsqueda no guardó la ruta completa: solo dejó migas de pan en
    # `anterior`. Se camina hacia atrás (destino -> ... -> origen)
    # siguiéndolas y luego se voltea la lista para dejarla en el sentido
    # real del viaje.
    ruta = []
    estacion = destino
    while estacion is not None:
        ruta.append(estacion)
        estacion = anterior[estacion][0]
    ruta.reverse()

    return {"ruta": ruta, "distancia_total_km": distancia[destino]}


def buscar_tramo(estacion_a, estacion_b):
    """
    Busca en la BASE DE CONOCIMIENTO (la lista TRAMOS, que es la red fija)
    el tramo que une dos estaciones.

    No consulta rutas ni viajes anteriores, porque el sistema no
    guarda historial; cada búsqueda parte siempre de la misma red. Esta
    función solo se usa para armar el itinerario final (obtener la
    distancia de cada par de estaciones consecutivas de la ruta).
    """
    for tramo in TRAMOS:
        if frozenset((tramo["origen"], tramo["destino"])) == frozenset((estacion_a, estacion_b)):
            return tramo
    return None


# ============================================================================
# 5. PLANIFICADOR: APLICA LAS REGLAS Y TOMA LA DECISIÓN DE RUTA
# ============================================================================
def planificar_viaje(origen, destino, contexto):
    """
    Aplica las reglas y busca la mejor ruta:

      1. La regla R1 define la velocidad (para estimar el tiempo de viaje).
      2. La regla R2 descarta los tramos cerrados y busca la mejor ruta férrea.
      3. Si la contingencia dejó sin ruta férrea, se calcula la ruta que
         existiría con la red completa y se marca en qué tramos se debe
         tomar un BUS (decisión multimodal por contingencia).
    """
    velocidad_kmh = regla_r1_clima(contexto)

    # R2: solo pueden usarse los tramos que pueden operarse en tren.
    tramos_operativos = [tramo for tramo in TRAMOS
                         if regla_r2_contingencia(tramo, contexto)]
    ruta = buscar_ruta_optima(origen, destino, construir_red(tramos_operativos))
    completa_en_tren = ruta is not None

    if ruta is None:
        # No quedó ruta férrea: se busca la ruta con la red completa para
        # poder sugerir el bus exactamente en los tramos cerrados.
        ruta = buscar_ruta_optima(origen, destino, construir_red(TRAMOS))
        if ruta is None:
            return None  # ni siquiera con toda la red hay conexión

    # Se arma el itinerario tramo por tramo marcando si va en tren o en bus.
    itinerario = []
    for desde, hasta in zip(ruta["ruta"], ruta["ruta"][1:]):
        tramo = buscar_tramo(desde, hasta)
        en_bus = not regla_r2_contingencia(tramo, contexto)
        itinerario.append({"desde": desde, "hasta": hasta,
                           "distancia_km": tramo["distancia_km"], "bus": en_bus})

    distancia_tren = sum(paso["distancia_km"] for paso in itinerario if not paso["bus"])
    distancia_bus = sum(paso["distancia_km"] for paso in itinerario if paso["bus"])

    return {
        "ruta": ruta["ruta"],
        "itinerario": itinerario,
        "completa_en_tren": completa_en_tren,
        "distancia_tren_km": distancia_tren,
        "distancia_bus_km": distancia_bus,
        "distancia_total_km": distancia_tren + distancia_bus,
        "velocidad_kmh": velocidad_kmh,
        "tiempo_tren_min": distancia_tren / velocidad_kmh * 60,
    }


# ============================================================================
# 6. PRESENTACIÓN DE RESULTADOS
# ============================================================================
def mostrar_resultado(origen, destino, contexto, resultado):
    """Muestra el plan de ruta y las reglas que sustentan la decisión."""
    print()
    print("=" * 70)
    print(f"  PLAN DE RUTA: {origen}  ->  {destino}")
    print("=" * 70)
    print(f"  Lluvia: {'sí' if contexto['lluvia'] else 'no'}")
    if contexto["tramos_bloqueados"]:
        cerrados = ", ".join(" - ".join(par) for par in contexto["tramos_bloqueados"])
    else:
        cerrados = "ninguno"
    print(f"  Tramos en contingencia: {cerrados}")

    if resultado is None:
        print("\n  RESULTADO: no existe conexión férrea entre esos puntos.")
        return

    print("\n  RUTA: " + "  ->  ".join(resultado["ruta"]))
    print("\n  ITINERARIO:")
    for paso in resultado["itinerario"]:
        medio = "BUS (tramo en contingencia)" if paso["bus"] else "tren"
        print(f"   - {paso['desde']} -> {paso['hasta']}: "
              f"{paso['distancia_km']} km en {medio}")

    horas = int(resultado["tiempo_tren_min"] // 60)
    minutos = int(resultado["tiempo_tren_min"] % 60)
    print(f"\n  Distancia total: {resultado['distancia_total_km']} km "
          f"(tren: {resultado['distancia_tren_km']} km"
          + (f" | bus: {resultado['distancia_bus_km']} km"
             if resultado["distancia_bus_km"] else "") + ")")
    print(f"  Tiempo estimado en tren: {resultado['tiempo_tren_min']:.0f} min "
          f"({horas} h {minutos} min) a {resultado['velocidad_kmh']} km/h")

    if not resultado["completa_en_tren"]:
        print("\n  SUGERENCIA (regla R2): la vía férrea está interrumpida;")
        print("  tome un BUS en el/los tramo(s) indicado(s) y continúe en tren.")

    print("\n  REGLAS APLICADAS:")
    print("   - R1 Clima: " + ("activada, velocidad 30 km/h por lluvia."
                              if contexto["lluvia"]
                              else "no activada, velocidad normal 50 km/h."))
    print("   - R2 Contingencia: " + ("activada, hay tramos cerrados."
                                      if contexto["tramos_bloqueados"]
                                      else "no activada, todas las vías operativas."))
    print("=" * 70)


def ejecutar_escenario(origen, destino, contexto):
    """Ejecuta un escenario completo: planifica el viaje y muestra el plan."""
    resultado = planificar_viaje(origen, destino, contexto)
    mostrar_resultado(origen, destino, contexto, resultado)


# ============================================================================
# 7. INTERFAZ DE USUARIO (MENÚ INTERACTIVO)
# ============================================================================
def pedir_opcion(mensaje, opciones_validas):
    """Pide al usuario una opción por consola hasta que sea válida."""
    while True:
        respuesta = input(mensaje).strip()
        if respuesta in opciones_validas:
            return respuesta
        print(f"   Opción no válida. Escriba una de: {', '.join(opciones_validas)}")


def escenario_personalizado():
    """Permite elegir el punto A y el punto B. El clima y los tramos en
    contingencia se deciden AL AZAR en cada petición de ruta."""
    print("\n   Estaciones de la red:")
    for indice, nombre in enumerate(ESTACIONES, start=1):
        print(f"    {indice}. {nombre}")

    def pedir_estacion(etiqueta):
        """Lee el número de una estación y devuelve su nombre."""
        while True:
            texto = input(f"   {etiqueta} (número): ").strip()
            if texto.isdigit() and 1 <= int(texto) <= len(ESTACIONES):
                return ESTACIONES[int(texto) - 1]
            print("   Número fuera del rango, intente de nuevo.")

    origen = pedir_estacion("Punto A (origen)")
    destino = pedir_estacion("Punto B (destino)")

    # Clima aleatorio: en cada petición de ruta se decide al azar si está
    llueve = generar_lluvia_aleatoria()
    print("   Clima del momento: " + ("lloviendo" if llueve else "despejado"))

    # Contingencias aleatorias: en cada petición de ruta se cierran al azar
    tramos_bloqueados = generar_contingencias_aleatorias(2)
    print("   Contingencias del momento (vías cerradas al azar):")
    for par in tramos_bloqueados:
        print(f"    - {par[0]} - {par[1]}")

    ejecutar_escenario(origen, destino,
                       crear_contexto(llueve, tramos_bloqueados))


def main():
    """Menú principal del sistema."""
    print("=" * 70)
    print("  SISTEMA EXPERTO - RED FERROVIARIA DE COLOMBIA")
    print("  Búsqueda de rutas basada en reglas (lluvia y contingencias)")
    print("=" * 70)

    while True:
        print("\n  MENÚ DE ESCENARIOS:")
        print("   1. Cali -> Bogotá Centro (condiciones normales)")
        print("   2. Cali -> Bogotá Centro (con lluvia)")
        print("   3. Facatativá -> Bogotá Centro (tramo Mosquera - Bogotá")
        print("      cerrado por contingencia)")
        print("   4. Escenario personalizado (A y B a elección; clima y dos")
        print("      tramos al azar)")
        print("   0. Salir")

        opcion = pedir_opcion("   Seleccione una opción: ",
                              ["0", "1", "2", "3", "4"])

        if opcion == "0":
            print("\n  ¡Hasta pronto! Misión cumplida.")
            break
        elif opcion == "1":
            ejecutar_escenario("Cali", "Bogotá Centro", crear_contexto())
        elif opcion == "2":
            ejecutar_escenario("Cali", "Bogotá Centro",
                               crear_contexto(lluvia=True))
        elif opcion == "3":
            ejecutar_escenario("Facatativá", "Bogotá Centro",
                               crear_contexto(tramos_bloqueados=[
                                   ("Mosquera", "Bogotá Centro")]))
        elif opcion == "4":
            escenario_personalizado()


# Punto de entrada del programa cuando se ejecuta como script principal.
if __name__ == "__main__":
    main()
