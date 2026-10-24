"""Genera los notebooks del proyecto (notebooks/*.ipynb). Se corre una vez; después se editan en Jupyter."""
from pathlib import Path

import nbformat as nbf

NB = Path(__file__).resolve().parent.parent / "notebooks"
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell


def save(name, cells):
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbf.write(nb, NB / name)


LOAD = """import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["figure.figsize"] = (11, 4)

COIN = "BTC"   # cambiá a "ETH" o "SOL" para mirar otra moneda
df = pd.read_csv(f"../data/{COIN}.csv", parse_dates=["time"])"""

save("01_explorar.ipynb", [
    md("""# 01 · Explorar los datos

Antes de buscar patrones hay que **conocer los datos** y comprobar que están bien. Si los datos están mal, todo lo que venga después también.

Los datos están en `data/BTC.csv`: un **CSV**, que es una tabla guardada como texto (como un Excel simple). Cada fila es una hora y tiene tres columnas:
- `time`: la hora.
- `close`: el precio al cierre de esa hora.
- `fundingRate`: el **funding**, el pago que cada hora se hacen entre sí los que apuestan a que sube (*longs*) y los que apuestan a que baja (*shorts*). Si es **positivo**, los longs le pagan a los shorts: hay más gente apostando a la suba de la que el mercado "necesita"."""),
    md("## 1. Cargar la tabla\n`pd.read_csv` lee el archivo y lo convierte en una tabla de pandas (un *DataFrame*). `head()` muestra las primeras filas."),
    code(LOAD + "\ndf.head()"),
    md("## 2. Resumen rápido\n`describe()` da, para cada columna, cuántos datos hay, el promedio, el mínimo, el máximo, etc. Mirá si los números tienen sentido."),
    code("df.describe()"),
    md("""## 3. ¿Hay huecos?

Un **hueco** es una hora sin dato. Si faltan muchas horas seguidas, los cálculos de "las próximas 8 horas" quedan mal.
- `isna().sum()`: cuántos valores vacíos tiene cada columna.
- La segunda parte busca horas que faltan en la secuencia (debería haber una fila cada 1 hora exacta)."""),
    code("""print("Valores vacíos por columna:")
print(df.isna().sum())

saltos = df["time"].diff().dropna()
print("\\nSaltos entre filas distintos de 1 hora:", (saltos != pd.Timedelta("1h")).sum())"""),
    md("""## 4. ¿Hay valores raros?

Un **valor raro** (*outlier*) es un número muy lejos de lo normal: puede ser un error de los datos o un evento real (un crash, una liquidación masiva). No se borran sin pensar: se miran y se decide.

Acá buscamos el retorno por hora (cuánto cambió el precio de una hora a la siguiente) más grande y más chico."""),
    code("""df["ret_1h"] = df["close"].pct_change()
print("Mayores subas en 1 hora:")
print(df.nlargest(3, "ret_1h")[["time", "close", "ret_1h"]])
print("\\nMayores caídas en 1 hora:")
print(df.nsmallest(3, "ret_1h")[["time", "close", "ret_1h"]])"""),
    md("## 5. Graficar el precio\n`plot` dibuja una columna contra otra. El eje horizontal es el tiempo, el vertical el precio."),
    code("""df.plot(x="time", y="close", title=f"{COIN}: precio por hora", legend=False)
plt.ylabel("USD"); plt.show()"""),
    md("## 6. Graficar el funding\nMultiplicamos por 100 para verlo en %. Fijate si suele ser positivo, si tiene picos y cuándo."),
    code("""(df.set_index("time")["fundingRate"] * 100).plot(title=f"{COIN}: funding rate por hora (%)")
plt.axhline(0, color="black", lw=0.8); plt.ylabel("% por hora"); plt.show()

print(f"Horas con funding positivo: {(df.fundingRate > 0).mean():.0%}")"""),
    md("""## Qué anotar antes de seguir
- ¿Hay huecos? ¿Cuántos?
- ¿Algún valor raro? ¿Fue un evento real (buscá la fecha en X o en noticias)?
- ¿El funding suele ser positivo o negativo? ¿Tiene picos?

Estas respuestas van en la sección **Datos** del README."""),
])

save("02_funding.ipynb", [
    md("""# 02 · ¿El funding predice el precio?

**La idea:** cuando el funding está muy alto, hay muchísima gente apostando a la suba (pagan caro por mantener su apuesta). Si el precio no sube, muchos cierran o los liquidan, y eso empuja el precio **para abajo**. Si fuera cierto, un funding muy alto anunciaría bajas.

**La pregunta:** ¿el funding extremo de esta hora predice cuánto se mueve el precio en las **próximas 8 horas**?

Pasos:
1. Calcular, para cada hora, cuánto se movió el precio en las 8 horas **siguientes**.
2. Medir qué tan **extremo** es el funding de cada hora comparado con lo normal de esa semana.
3. Ordenar todas las horas de menor a mayor funding, partirlas en **5 grupos iguales** y ver el movimiento promedio del precio en cada grupo."""),
    code(LOAD),
    md("""## Paso 1: el retorno futuro

`shift(-8)` toma el precio de 8 filas más adelante (8 horas después). El retorno futuro es cuánto cambió en % desde ahora hasta entonces.

**Esta es la variable que queremos predecir.** Ojo: solo se usa para medir; jamás puede entrar en la regla, porque en la vida real el futuro no se conoce."""),
    code("""H = 8  # horizonte en horas: probá también 4 y 24
df["fut_ret"] = df["close"].shift(-H) / df["close"] - 1
df[["time", "close", "fut_ret"]].head(10)"""),
    md("""## Paso 2: ¿qué tan extremo es el funding? (el *z-score*)

Un funding de 0,001 % puede ser alto en una semana tranquila y normal en una semana loca. Por eso lo comparamos con **su propia semana anterior** (168 horas):

`z = (funding de ahora − promedio de la última semana) / desvío de la última semana`

- `z = 0`: funding normal.
- `z = +2`: mucho más alto de lo habitual.
- `z = −2`: mucho más bajo de lo habitual.

`rolling(168)` calcula el promedio y el desvío usando solo las 168 horas **anteriores**, así no usamos información del futuro."""),
    code("""W = 168
media = df["fundingRate"].rolling(W).mean()
desvio = df["fundingRate"].rolling(W).std()
df["z"] = (df["fundingRate"] - media) / desvio

df = df.dropna(subset=["z", "fut_ret"])  # las primeras horas no tienen semana anterior
df["z"].hist(bins=60); plt.title("Distribución del z-score del funding"); plt.show()"""),
    md("""## Paso 3: los 5 grupos

`pd.qcut(..., 5)` ordena las horas por su z y las parte en 5 grupos del mismo tamaño:
- Grupo 1: el 20 % de horas con el funding **más bajo**.
- Grupo 5: el 20 % con el funding **más alto**.

Después calculamos el retorno futuro promedio de cada grupo."""),
    code("""df["grupo"] = pd.qcut(df["z"], 5, labels=[1, 2, 3, 4, 5])
tabla = df.groupby("grupo", observed=True)["fut_ret"].agg(["mean", "count"])
tabla["mean %"] = tabla["mean"] * 100
print(tabla[["mean %", "count"]])

(tabla["mean %"]).plot.bar(title=f"{COIN}: retorno promedio de las próximas {H} h según el funding")
plt.xlabel("grupo (1 = funding más bajo · 5 = más alto)"); plt.ylabel("%"); plt.axhline(0, color="black", lw=0.8); plt.show()"""),
    md("""## Cómo leer el gráfico

- **Si las barras bajan de forma ordenada del 1 al 5** (o suben), hay una **posible señal**: el funding dice algo del precio futuro.
- **Si las barras están desordenadas o son todas parecidas**, **no hay señal**. Es un resultado válido y se publica igual.

**Cuidado:** con pocos meses de datos, una diferencia chica puede ser pura casualidad. Por eso existe el notebook 03."""),
    md("## Extra: ¿se repite en otras monedas?\nSi el patrón es real, debería aparecer también en ETH y SOL. Si solo aparece en una, sospechá de casualidad."),
    code("""for coin in ["BTC", "ETH", "SOL"]:
    d = pd.read_csv(f"../data/{coin}.csv", parse_dates=["time"])
    d["fut_ret"] = d["close"].shift(-H) / d["close"] - 1
    d["z"] = (d["fundingRate"] - d["fundingRate"].rolling(W).mean()) / d["fundingRate"].rolling(W).std()
    d = d.dropna(subset=["z", "fut_ret"])
    g = d.groupby(pd.qcut(d["z"], 5, labels=[1, 2, 3, 4, 5]), observed=True)["fut_ret"].mean() * 100
    print(coin, " · ".join(f"G{k}: {v:+.3f}%" for k, v in g.items()))"""),
])

save("03_backtest.ipynb", [
    md("""# 03 · Backtest honesto

Un **backtest** es simular qué habría pasado si hubiéramos operado con una regla en el pasado. Es fácil engañarse, así que seguimos tres reglas:

1. **Dividir en el tiempo.** Elegimos la regla mirando solo los **primeros 2/3** de los datos y la probamos en el **último 1/3**, que no miramos. Es como estudiar con unos ejercicios y rendir con otros.
2. **Pagar comisiones** en cada operación, y el **funding** mientras la posición está abierta.
3. **Probar variaciones.** Si solo funciona en un caso exacto, probablemente fue suerte.

**La regla:** si el z del funding supera un umbral, apostamos a la **baja** durante H horas (*short*). Si es menor que menos el umbral, apostamos a la **suba** (*long*)."""),
    code(LOAD + """
H = 8
COMISION = 0.00035  # 0,035 % por operación (verificá la tarifa vigente de Hyperliquid)
W = 168
df["z"] = (df["fundingRate"] - df["fundingRate"].rolling(W).mean()) / df["fundingRate"].rolling(W).std()
df = df.dropna(subset=["z"]).reset_index(drop=True)"""),
    md("""## La simulación

Recorre las horas en orden. Si no hay posición abierta y el z cruza el umbral, abre una y la mantiene H horas. El resultado de cada operación es:

`resultado = dirección × retorno del precio − 2 comisiones (entrar y salir) − dirección × funding pagado`

(dirección = +1 si es long, −1 si es short; un long paga el funding cuando es positivo y un short lo cobra)."""),
    code("""def backtest(d, umbral, H=H):
    ops, i = [], 0
    while i < len(d) - H:
        z = d.at[i, "z"]
        if abs(z) >= umbral:
            dir_ = -1 if z > 0 else 1
            ret = d.at[i + H, "close"] / d.at[i, "close"] - 1
            fund = d["fundingRate"].iloc[i + 1:i + H + 1].fillna(0).sum()
            ops.append({"time": d.at[i, "time"], "dir": dir_, "pnl": dir_ * ret - 2 * COMISION - dir_ * fund})
            i += H  # no abrimos otra hasta cerrar esta
        else:
            i += 1
    return pd.DataFrame(ops)


def medir(ops, nombre=""):
    if ops.empty:
        return {"nombre": nombre, "ops": 0}
    curva = ops["pnl"].cumsum()
    por_año = len(ops) / ((ops.time.max() - ops.time.min()).days / 365 + 1e-9)
    return {
        "nombre": nombre,
        "ops": len(ops),
        "ganancia total %": round(ops.pnl.sum() * 100, 2),
        "aciertos %": round((ops.pnl > 0).mean() * 100, 1),
        "sharpe": round(ops.pnl.mean() / ops.pnl.std() * np.sqrt(por_año), 2) if ops.pnl.std() > 0 else None,
        "peor caída %": round((curva - curva.cummax()).min() * 100, 2),
    }"""),
    md("""## Paso 1: elegir el umbral **solo con el período de entrenamiento**

Probamos tres umbrales en los primeros 2/3 y nos quedamos con el mejor. El período de prueba todavía no se toca."""),
    code("""corte = int(len(df) * 2 / 3)
train, test = df.iloc[:corte].reset_index(drop=True), df.iloc[corte:].reset_index(drop=True)
print("Entrenamiento:", train.time.min().date(), "→", train.time.max().date())
print("Prueba:       ", test.time.min().date(), "→", test.time.max().date())

res = pd.DataFrame([medir(backtest(train, u), f"umbral {u}") for u in [1.5, 2.0, 2.5]])
res"""),
    md("""## Paso 2: la prueba de verdad

Usamos el umbral elegido en el período de **prueba**, que nunca miramos. **Este es el resultado que cuenta.**

- Si gana en entrenamiento pero pierde en prueba: era casualidad (*sobreajuste*).
- Si gana en los dos: posible señal, pero hay que seguir probando."""),
    code("""mejor = float(res.sort_values("ganancia total %", ascending=False).iloc[0]["nombre"].split()[-1])
ops = backtest(test, mejor)
print(medir(ops, f"PRUEBA · umbral {mejor}"))

if not ops.empty:
    (ops.set_index("time")["pnl"].cumsum() * 100).plot(title=f"{COIN}: ganancia acumulada en el período de prueba (%)")
    plt.axhline(0, color="black", lw=0.8); plt.ylabel("%"); plt.show()"""),
    md("""## Paso 3: robustez

¿Funciona también en otras monedas y con otros horizontes? Si la ganancia aparece solo en una combinación exacta, lo más probable es que sea suerte."""),
    code("""filas = []
for coin in ["BTC", "ETH", "SOL"]:
    d = pd.read_csv(f"../data/{coin}.csv", parse_dates=["time"])
    d["z"] = (d["fundingRate"] - d["fundingRate"].rolling(W).mean()) / d["fundingRate"].rolling(W).std()
    d = d.dropna(subset=["z"]).reset_index(drop=True)
    t = d.iloc[int(len(d) * 2 / 3):].reset_index(drop=True)
    for h in [4, 8, 24]:
        filas.append(medir(backtest(t, mejor, H=h), f"{coin} · {h} h"))
pd.DataFrame(filas)"""),
    md("""## Glosario de los resultados
- **ops:** cuántas operaciones hizo.
- **ganancia total %:** la suma de todas las operaciones, ya con comisiones y funding.
- **aciertos %:** qué porcentaje de operaciones ganó.
- **sharpe:** ganancia por unidad de riesgo, llevada a un año. Arriba de 1 es bueno; arriba de 2, sospechosamente bueno (revisá que no haya un error).
- **peor caída %:** lo máximo que llegó a perder desde un pico. Mide cuánto dolor aguantás.

## Qué escribir en el README
- El resultado del **período de prueba** (no el de entrenamiento).
- La tabla de robustez.
- Las limitaciones: pocos meses, un solo tipo de mercado, comisiones aproximadas, sin deslizamiento."""),
])
print("notebooks creados")
