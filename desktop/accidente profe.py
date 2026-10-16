import matplotlib.pyplot as plt
import pandas as pd

# 1. Definición de los datos iniciales
datos = {
    "Categoría": [
        "Tiempo laboral perdido",
        "Reparación de la bicicleta",
        "Medicamentos",
        "Elementos de protección",
        "Atención médica",
        "Transporte",
    ],
    "Costo": [400000, 350000, 280000, 180000, 100000, 80000],
}

# Crear DataFrame
df = pd.DataFrame(datos)

# Calcular porcentajes
costo_total = df["Costo"].sum()
df["Porcentaje"] = (df["Costo"] / costo_total) * 100

print("--- TABLA DE COSTOS Y PORCENTAJES ---")
print(df.to_string(index=False))
print(f"\nCosto Total: ${costo_total:,.0f}\n")

# 2. Generar el gráfico de barras horizontales
# Ordenamos de menor a mayor para que al graficar en barras horizontales aparezca de mayor a arriba
df_sorted = df.sort_values(by="Costo", ascending=True)

plt.figure(figsize=(10, 6))
barras = plt.barh(
    df_sorted["Categoría"], df_sorted["Costo"], color="skyblue", edgecolor="grey"
)

plt.title(
    "Costos del accidente por categoría", fontsize=14, fontweight="bold", pad=15
)
plt.xlabel("Costo ($)", fontsize=12)
plt.ylabel("Categoría", fontsize=12)

# Añadir las etiquetas de los valores dentro de las barras
for barra in barras:
  width = barra.get_width()
  plt.text(
      width + 10000,
      barra.get_y() + barra.get_height() / 2,
      f"${width:,.0f}",
      va="center",
      ha="left",
      fontsize=10,
      fontweight="semibold",
  )

plt.xlim(0, max(df["Costo"]) * 1.25)  # Espacio para las etiquetas
plt.grid(axis="x", linestyle="--", alpha=0.7)
plt.tight_layout()

# Mostrar gráfico
plt.show()


# 3. Simulación del modelo de escenarios (Días perdidos vs Ingreso Diario)
def calcular_costo_total(dias_perdidos, ingreso_diario):
  # Suma de los otros 5 componentes fijos: 990,000
  gastos_fijos = 990000
  return gastos_fijos + (dias_perdidos * ingreso_diario)


print("--- MODELO DE ESCENARIOS ---")
ingreso_ejemplo = 50000
dias_ejemplo = 8
resultado_ejemplo = calcular_costo_total(dias_ejemplo, ingreso_ejemplo)

print(f"Supuesto ingreso diario: ${ingreso_ejemplo:,.0f}")
print(f"Días perdidos simulados: {dias_ejemplo}")
print(
    f"Costo total estimado del escenario: ${resultado_ejemplo:,.0f} (Coincide"
    " con los $1.390.000 iniciales)"
)