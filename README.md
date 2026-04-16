# 🔒 Explicación del Código - Actividad 1 (Cifrado Paralelo)

Este documento fue creado para explicar a detalle la función de cada código dentro de la carpeta `actividad_1_codigo_base` y cómo se relacionan entre sí para cumplir con la rúbrica del control.

El objetivo principal del proyecto fue **paralelizar el algoritmo de cifrado AES en modo CTR** usando Python, analizar su rendimiento (Speedup y Eficiencia) y compararlo con el algoritmo secuencial base, además de incluir demostraciones del modo CBC.

---

## 📂 Archivos Base y Utilidades

Estos archivos nos permitieron preparar el entorno y validar datos:

- **`generate_files.py`**
  Genera archivos `CSV` de gran tamaño con datos simulados (textos basura) para usarlos en nuestras pruebas de estrés (tamaños desde unos megas a más de un Gigabyte).

- **`validador.py`**
  Este script compara bit a bit dos archivos distintos (por ejemplo, el archivo *original* y el archivo *descifrado* final). Si los datos no coinciden exactamente lanza un error. Sirve para corroborar que nunca se corrompen los datos durante el cifrado/descifrado por chunks en paralelo.

---

## 🛡️ Los Archivos de Cifrado (Versión Secuencial vs Paralela)

- **`cifrado_aes_ctr_secuencial.py`**
  Es nuestra base o punto de comparación. Cifra o descifra el archivo de manera tradicional en un solo hilo (*single-thread*). Fue indispensable para luego poder evaluar los tiempos "Base" en nuestros gráficos de rendimiento.
  
- **`cifrado_aes_ctr_paralelo.py`** (El core de la actividad)
  Es el script modificado en donde se implementó paralelismo a través de la librería mutliprocesos de Python (`ProcessPoolExecutor`). ¿Cómo funciona?
  1. No lee de golpe todo el archivo pesado usando la memoria RAM, lo **divide en bloques pequeños** (chunks).
  2. Cada "chunk" o parte del archivo se le delega a un núcleo disponible del procesador para que la cifre/descifre.
  3. Esto es posible en  **AES-CTR** porque cada bloque tiene un "contador" independiente, es decir, el bloque de la posición de memoria `A` se puede procesar sin necesidad de haber procesado antes el bloque de memoria anterior.

---

## 🧪 Pruebas de Rendimiento y Gráficos (Experimentos)

Para demostrar lo que hicimos en el laboratorio o informe, necesitábamos capturar datos de rendimiento:

- **`experimentos.py`**
  Es el *script de orquestación*. En lugar de correr los scripts a mano uno a la vez (lo cual tardaría horas), este programa toma archivos de distintos tamaños, corre el programa secuencial, luego el programa paralelo con 1, 2, 4, 8, ... trabajadores (núcleos), saca los promedios de tiempo, y finalmente los exporta a un documento llamado `resultados_experimento_oficial.csv`.

- **`generar_graficos.py`**
  Toma los datos del CSV anterior (`resultados_experimento_oficial.csv`) y usa Python (`matplotlib` y `seaborn`) para generar los 3 gráficos fundamentales de rendimiento técnico:
  1. **Gráfico de Tiempo:** Cuánto demora el algoritmo vs cantidad de hilos/workers.
  2. **Gráfico de Speedup:** Cuántas veces rápido fuimos comparados con la base en función a recursos añadidos.
  3. **Gráfico de Eficiencia:** El ratio de qué tan bien estamos sacándole provecho a cada núcleo "extra" agregado al sistema.

---

## 🎁 El Bonus: Demostración Matemática-Práctica de CBC

- **`experimento_cbc_bonus.py`** y **`cifrado_aes_cbc_experimental.py`**
  Según la teoría criptográfica, el modo **CBC** (Cipher Block Chaining) encripta generando una cadena interdependiente: el bloque #2 no puede encriptarse si el bloque #1 no ha finalizado. 
  Creamos estos programas para **intentar paralelizar CBC**, ¿El resultado? Demostramos en un gráfico adicional (`grafico_bonus_cbc.png`) que el modo "Paralelo en CBC" de hecho funciona más lento que la versión secuencial debido al "inter-bloqueo". Es una excelente forma práctica de demostrar conocimiento avanzado del tema ante el evaluador.

---

## 🚀 Flujo de Ejecución (Para mostrarle al Profesor)

Si van a demostrar cómo funciona, este es el orden "lógico" del cómo se debe correr todo:

1. **Paso 1:** Rebotar Python en consola para crear archivos de prueba pesados en megas (ej. 100MB):
   ```bash
   python generate_files.py 100 prueba.csv
   ```
2. **Paso 2:** En caso de no tener los gráficos hechos o querer re-hacerlos todo en un click, correr el experimento. Se demorará varios minutos porque prueba múltiples iteraciones:
   ```bash
   python experimentos.py
   ```
3. **Paso 3:** Una vez generado o creado el archivo de `resultados_experimento_oficial.csv`, corren:
   ```bash
   python generar_graficos.py
   ```
   **¡Y voilá!, las métricas están construidas automáticamente en PNG.**

> **Nota para el equipo:** 
> Todos los archivos gigantes de resultados (1 Gigabyte, etc.) han sido excluidos del sistema por el archivo `.gitignore` para no colapsar nuestro GitHub. Cuando bajen el proyecto desde Git y deseen reacer gráficos muy pesados, deberán volver a correr `generate_files.py` en tamaño 1024 (1 GB) en local en sus máquinas.
