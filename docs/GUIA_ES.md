# Hyperliquid Research · Guía en español

> Esta es la guía completa en español. El README principal del repositorio está en inglés. Los resultados se completan en el README.

Research cuantitativo público sobre el mercado de futuros perpetuos de **Hyperliquid**.

**Pregunta principal:** ¿el *funding rate* extremo predice hacia dónde se mueve el precio en las próximas horas?

**Pregunta siguiente:** ¿los saltos de *interés abierto* y las *liquidaciones* anticipan movimientos fuertes (volatilidad)?

> Estado: 🟡 en curso. Todo se publica, incluso lo que no funcione. "No hay señal" también es un resultado.

---

## 1. Qué es todo esto (en simple)

**Hyperliquid** es un exchange donde la gente opera **futuros perpetuos** ("perps"): apuestas con apalancamiento a que una moneda sube (**long**) o baja (**short**), sin fecha de vencimiento.

**Funding rate.** Como un perpetuo no vence, hace falta algo que mantenga su precio pegado al precio real de la moneda. Ese algo es el *funding*: un pago que se hacen entre sí longs y shorts **cada hora**.
- Funding **positivo**: los longs les pagan a los shorts. Hay más gente apostando a la suba de lo normal.
- Funding **negativo**: los shorts les pagan a los longs. Hay más gente apostando a la baja.

**Interés abierto (open interest).** Cuántos contratos hay abiertos en total en ese momento. Si sube, entra dinero nuevo a apostar; si baja, la gente cierra posiciones.

**Liquidación.** Cuando alguien apalancado pierde demasiado, el exchange le cierra la posición a la fuerza. Muchas liquidaciones juntas empujan el precio todavía más en la misma dirección (efecto cascada).

### La idea que queremos comprobar

Si el funding está **muy alto**, hay demasiada gente apostando a la suba y pagando caro por sostenerla. Si el precio no acompaña, empiezan a cerrar o los liquidan, y eso **empuja el precio para abajo**. Al revés con funding muy negativo.

¿Pasa de verdad, o es un mito? Eso es lo que mide este proyecto. Ya sabemos que muchas ideas "obvias" no se cumplen en los datos: por eso se miden.

---

## 2. Qué hay en el proyecto

```
hyperliquid-research/
├── README.md              ← el proyecto en inglés y (al final) los resultados
├── docs/GUIA_ES.md        ← esta guía
├── requirements.txt       ← las librerías de Python que usa
├── data/                  ← los datos
│   ├── HYPE.csv, BTC.csv, ETH.csv, SOL.csv   ← precio y funding de cada hora
│   └── oi/                ← interés abierto grabado por collector.py
├── scripts/
│   ├── download.py        ← baja de la API de Hyperliquid precio y funding por hora
│   ├── collector.py       ← graba el interés abierto cada minuto (dejarlo corriendo)
│   └── make_notebooks.py  ← crea los notebooks (ya está hecho; no hace falta volver a correrlo)
└── notebooks/
    ├── 01_explorar.ipynb  ← mirar los datos: ¿están bien? gráficos
    ├── 02_funding.ipynb   ← la pregunta: ¿el funding predice el precio?
    └── 03_backtest.ipynb  ← la prueba honesta: ¿se podría ganar dinero con eso?
```

**Glosario rápido**
- **CSV:** una tabla guardada como texto (como un Excel simple). Cada línea es una fila.
- **pandas:** la librería de Python para trabajar con tablas.
- **Jupyter / notebook (.ipynb):** un cuaderno donde el código va en bloques; ejecutás un bloque y ves el resultado o el gráfico justo abajo.
- **Los datos de este proyecto:** las últimas ~200 días (unas 4.800 horas). Para cada hora: el precio de la moneda y el funding de esa hora.

---

## 3. Cómo usarlo

Cada vez que abras la terminal:

```bash
cd ~/hyperliquid-research
source .venv/bin/activate     # activa el entorno del proyecto
```

| Para… | Comando |
|---|---|
| Actualizar los datos | `python scripts/download.py` |
| Grabar el interés abierto (dejarlo corriendo en otra terminal) | `python scripts/collector.py` |
| Abrir los notebooks | `jupyter notebook` → se abre el navegador → carpeta `notebooks` |

En un notebook: hacé clic en un bloque y apretá **Shift + Enter** para ejecutarlo. Ejecutalos en orden, de arriba hacia abajo.

Si alguna vez instalás todo desde cero: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

---

## 4. El research paso a paso (qué hacer y qué buscar)

### Paso 1 · Conocer los datos (`01_explorar`)
Ejecutá el notebook y anotá:
- [ ] ¿Faltan horas (huecos)? ¿Cuántas?
- [ ] ¿Hay movimientos raros (subas o caídas enormes en 1 hora)? Buscá esas fechas en X o en noticias: ¿fue un evento real?
- [ ] ¿El funding suele ser positivo o negativo? ¿Cuándo tuvo picos?

### Paso 2 · La pregunta (`02_funding`)
El notebook ordena todas las horas de menor a mayor funding, las parte en 5 grupos iguales y calcula, para cada grupo, cuánto se movió el precio en las 8 horas siguientes.
- [ ] Mirá el gráfico de 5 barras. **¿Bajan o suben de forma ordenada del grupo 1 al 5?** → posible señal. **¿Desordenadas o parecidas?** → no hay señal.
- [ ] Repetí con `H = 4` y `H = 24` (cambiá el número en el notebook).
- [ ] Mirá el resultado de ETH y SOL al final: **¿se repite el patrón?** Si solo aparece en una moneda, sospechá de casualidad.

### Paso 3 · La prueba honesta (`03_backtest`)
Simula operar con una regla simple: *si el funding está muy alto, apuesto a la baja 8 horas; si está muy bajo, a la suba*.
- Elige el umbral mirando solo los **primeros 2/3** de los datos y lo prueba en el **último 1/3**, que nunca miró. **Solo cuenta el resultado de esa prueba.**
- Descuenta comisiones (0,035 % por operación) y el funding pagado.
- [ ] ¿Gana en el período de prueba, ya con comisiones?
- [ ] ¿Funciona también en ETH y SOL y con otros horizontes (tabla de robustez)?
- [ ] Si el Sharpe da altísimo (más de 2 o 3), **desconfiá**: casi siempre es un error.

### Paso 4 · Interés abierto y liquidaciones (próximo)
- Dejá `collector.py` grabando desde ya: necesita **4 a 6 semanas** de datos.
- Pregunta: ¿un salto grande de interés abierto anticipa un movimiento fuerte en la próxima hora?
- Hay que compararlo con una referencia simple: "la próxima hora se mueve igual que la última". Si el modelo no le gana a eso, no sirve.
- Pendiente: investigar cómo obtener liquidaciones (websocket de trades de Hyperliquid).

### Paso 5 · Escribir los resultados (sección 6 del README)
Pregunta, datos, método, 2 o 3 gráficos, **qué no funcionó** y conclusión con el nivel de confianza.

---

## 5. Reglas del proyecto

1. **Nunca usar el futuro.** Toda regla usa solo datos disponibles en ese momento. El retorno futuro se usa únicamente para medir.
2. **Separar en el tiempo:** decidir con una parte de los datos, probar con otra que no se miró.
3. **Siempre con comisiones.** Una estrategia que gana antes de comisiones y pierde después, no sirve.
4. **Publicar lo que falla.** Un "no hay señal" bien hecho vale tanto como un hallazgo.
5. **Cero dinero real.** Esto es research, no trading.

**Errores típicos que hay que evitar:** usar datos del futuro sin darse cuenta; probar 50 variantes y mostrar solo la que ganó; olvidar comisiones; sacar conclusiones con pocas operaciones.

---

## 6. Resultados

*(Completar al terminar cada paso.)*

| Paso | Resultado | Fecha |
|---|---|---|
| Datos | | |
| ¿El funding predice el precio? | | |
| Backtest (período de prueba) | | |
| Robustez | | |

**Qué no funcionó y limitaciones:**

**Conclusión:**

---

## 7. Plan de publicación en X

1. **Al empezar:** "Empiezo un research público: ¿el funding rate de Hyperliquid predice el precio? Publico todo, incluso lo que falle."
2. **Durante:** un gráfico del notebook 01 o 02 con una frase de qué muestra.
3. **Al final:** un hilo con la pregunta, el gráfico de las 5 barras, el resultado del backtest, lo que no funcionó y el link a este repositorio.

## Datos

Fuente: API pública de Hyperliquid (`https://api.hyperliquid.xyz/info`): `fundingHistory`, `candleSnapshot` (velas de 1 hora) y `metaAndAssetCtxs` (interés abierto actual).
