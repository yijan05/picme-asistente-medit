class SkillQuestConsola:
    def __init__(self):
        # Inicialización del catálogo de carreras definido en el alcance[cite: 2]
        self.profesiones = [
            {"nombre": "Administración de Empresas", "puntaje": 0},
            {"nombre": "Medicina", "puntaje": 0},
            {"nombre": "Ingeniería de Sistemas", "puntaje": 0},
            {"nombre": "Derecho", "puntaje": 0},
            {"nombre": "Ingeniería Civil", "puntaje": 0}
        ]

    def sumar_puntos(self, indice_profesion, puntos):
        # Asignación de puntajes basada en las decisiones del jugador[cite: 2]
        self.profesiones[indice_profesion]["puntaje"] += puntos

    def iniciar_simulacion(self):
        print("=================================================")
        print("   BIENVENIDO A SKILLQUEST - MODO CONSOLA")
        print("=================================================\n")

        # Escenario 1: Ingeniería de Sistemas[cite: 2]
        print("[Escenario: Empresa Tecnológica]")
        print("El sistema principal de ventas se ha caído por un error en el código. ¿Qué decides hacer?")
        print("1. Revisar los bloques de código para encontrar el 'bug' y plantear una solución algorítmica.")
        print("2. Reasignar presupuesto de otro departamento para contratar a un consultor experto de inmediato.")
        print("3. Revisar los contratos de los clientes para anticipar posibles demandas por incumplimiento.")
        
        try:
            respuesta = int(input("Elige una opción (1-3): "))
            if respuesta == 1:
                self.sumar_puntos(2, 20)  # Sistemas
            elif respuesta == 2:
                self.sumar_puntos(0, 15)  # Administración
            elif respuesta == 3:
                self.sumar_puntos(3, 15)  # Derecho
        except ValueError:
            print("Entrada inválida. Avanzando al siguiente escenario...\n")

        # Escenario 2: Medicina[cite: 2]
        print("\n[Escenario: Hospital Universitario]")
        print("Llegan tres pacientes a urgencias al mismo tiempo. ¿Cómo procedes?")
        print("1. Analizo rápidamente los síntomas para priorizar la atención según la gravedad de cada uno.")
        print("2. Evalúo la distribución física de la sala de espera para optimizar el flujo de camillas.")
        print("3. Organizo turnos rotativos para que el personal de enfermería no se sature.")
        
        try:
            respuesta = int(input("Elige una opción (1-3): "))
            if respuesta == 1:
                self.sumar_puntos(1, 20)  # Medicina
            elif respuesta == 2:
                self.sumar_puntos(4, 15)  # Ing. Civil
            elif respuesta == 3:
                self.sumar_puntos(0, 15)  # Administración
        except ValueError:
            print("Entrada inválida. Avanzando al siguiente escenario...\n")

        # Escenario 3: Ingeniería Civil[cite: 2]
        print("\n[Escenario: Proyecto de Construcción]")
        print("Durante la supervisión de obra, detectas que faltan materiales esenciales. ¿Qué acción tomas?")
        print("1. Reviso las normativas vigentes para aplicar penalizaciones legales al proveedor.")
        print("2. Calculo la estabilidad temporal de la estructura para determinar si es seguro pausar la obra.")
        print("3. Diseño una herramienta de software básica para automatizar el control del inventario.")
        
        try:
            respuesta = int(input("Elige una opción (1-3): "))
            if respuesta == 1:
                self.sumar_puntos(3, 15)  # Derecho
            elif respuesta == 2:
                self.sumar_puntos(4, 20)  # Ing. Civil
            elif respuesta == 3:
                self.sumar_puntos(2, 15)  # Sistemas
        except ValueError:
            print("Entrada inválida. Avanzando al siguiente escenario...\n")

        # Escenario 4: Derecho[cite: 2]
        print("\n[Escenario: Firma de Abogados]")
        print("Un cliente es acusado injustamente. ¿Cuál es tu estrategia principal?")
        print("1. Leo detalladamente los hechos para construir argumentos sólidos y seleccionar la norma aplicable.")
        print("2. Solicito análisis médicos del acusado para demostrar inconsistencias biológicas en las pruebas.")
        print("3. Negocio los honorarios del bufete asegurando la rentabilidad de la firma antes de tomar el caso.")
        
        try:
            respuesta = int(input("Elige una opción (1-3): "))
            if respuesta == 1:
                self.sumar_puntos(3, 20)  # Derecho
            elif respuesta == 2:
                self.sumar_puntos(1, 15)  # Medicina
            elif respuesta == 3:
                self.sumar_puntos(0, 15)  # Administración
        except ValueError:
            print("Entrada inválida. Finalizando simulación...\n")

        self.generar_perfil_vocacional()

    # Módulo de Orientación Vocacional y Reportes[cite: 2]
    def generar_perfil_vocacional(self):
        # Función lambda para ordenar la lista de diccionarios de mayor a menor puntaje
        ranking = sorted(self.profesiones, key=lambda p: p["puntaje"], reverse=True)

        print("\n=================================================")
        print("         TU PERFIL VOCACIONAL GENERADO")
        print("=================================================")
        print("Basado en tus decisiones, este es tu nivel de afinidad:\n")

        for i, prof in enumerate(ranking):
            print(f"{i + 1}. {prof['nombre']} - Puntos: {prof['puntaje']}")

        print(f"\nRESULTADO FINAL: Tienes una clara vocación hacia {ranking[0]['nombre']}.")
        print("=================================================\n")


if __name__ == "__main__":
    juego = SkillQuestConsola()
    juego.iniciar_simulacion()