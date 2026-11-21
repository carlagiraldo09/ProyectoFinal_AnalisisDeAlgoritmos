# Proyecto final — Análisis de algoritmos

**Caso 2: Plataforma Pulso**

**Integrantes:** Carla Giraldo, Sara Regino, Alejandra Madrid y Laura Posada.

## Análisis del problema

### Contexto y proceso completo de Plataforma Pulso

Plataforma Pulso apoya el tamizaje de diabetes y recibe diariamente resultados
de 290 laboratorios e instituciones prestadoras de salud. Cada resultado
contiene el tipo y número de documento del paciente, el laboratorio y lote de
origen, la fecha del resultado, un índice de riesgo entre 0 y 100 y el
municipio. Como estos datos identifican personas y describen su estado de
salud, su integridad y confidencialidad son requisitos del proceso, no solo
características técnicas.

El flujo operativo estudiado comprende cuatro operaciones relacionadas:

1. **Consolidación de pacientes repetidos.** De los 1 450 000 resultados
   pendientes de un día típico, entre el 8 % y el 15 % corresponde a personas
   que ya aparecen en la plataforma. Para cada paciente debe conservarse
   únicamente el resultado más reciente, sin modificar los registros
   originales ni hacer desaparecer pacientes. El procedimiento actual compara
   cada resultado nuevo con la lista consolidada hasta encontrar su documento.
2. **Lista diaria de llamadas.** A partir de los resultados consolidados se
   deben seleccionar exactamente los 9 000 pacientes con mayor índice de
   riesgo. Cuando dos pacientes tienen el mismo índice, se atiende primero el
   resultado más antiguo. El proceso actual mantiene la lista mediante
   ordenamiento por inserción.
3. **Programación de unidades móviles.** Cada una de las nueve subregiones
   dispone de una unidad y recibe entre 40 y 120 solicitudes mensuales. Debe
   elegirse un conjunto de jornadas sin cruces. En este proyecto se maximiza la
   cantidad de pacientes de alto riesgo atendidos; esta es la operación
   desarrollada en el Laboratorio 4.
4. **Vigilancia de calidad de laboratorios.** Para cada laboratorio se busca el
   intervalo consecutivo de lotes con el mayor exceso acumulado de resultados
   positivos. Se procesan cerca de 30 lotes diarios por laboratorio y tres años
   de historia equivalen aproximadamente a 33 000 lotes por laboratorio. El
   procedimiento actual examina todos los subarreglos y puede tardar varios
   días.

Las operaciones de consolidación y lista de llamadas se ejecutan dentro de una
ventana nocturna de cuatro horas, entre la 01:00 y las 05:00. En conjunto, el
proceso actual tarda cerca de siete horas, por lo que no cumple esa ventana.
Este tiempo es una referencia combinada de ambas operaciones y no se atribuye
por completo a ninguna de ellas por separado.

El servidor disponible consume 380 W, ejecuta un solo hilo y no permite
distribuir el procesamiento. Además de la restricción temporal, el resultado
debe respetar las reglas funcionales: un registro vigente por paciente, una
lista de exactamente 9 000 llamadas, jornadas sin solapamientos y un intervalo
de vigilancia exactamente óptimo. Los registros originales de los
laboratorios deben permanecer sin alteraciones para conservar su trazabilidad.

### Alcance del proyecto

El proyecto implementará y comparará dos de las cuatro operaciones. La primera
es la programación de las jornadas de unidades móviles, ya terminada como parte
del Laboratorio 4 mediante intervalos ponderados. La segunda será la
consolidación de pacientes repetidos, para la cual se estudiarán diferentes
estructuras y estrategias antes de recomendar una solución.

Para ambas operaciones se presentarán al menos dos alternativas, análisis de
complejidad temporal y espacial, pruebas de corrección, mediciones con datos
sintéticos reproducibles y una estimación de energía. El análisis distinguirá
los resultados medidos de las extrapolaciones al volumen real y explicará sus
supuestos y limitaciones. También se examinarán las consecuencias de una
decisión incorrecta sobre la oportunidad de atención, la privacidad y la
equidad.

Las operaciones de selección de llamadas y vigilancia de laboratorios se
describen para comprender el proceso completo, pero no se implementarán. La
solución tampoco se integrará con sistemas clínicos reales ni utilizará datos
personales verdaderos. Por tratarse de un ejercicio académico, los datos serán
sintéticos y las recomendaciones constituirán un análisis algorítmico, no una
decisión clínica ni una validación jurídica del sistema.

### Modelo de la consolidación de pacientes

La segunda operación recibe una secuencia de resultados en el mismo orden en
que llegaron a la plataforma. Cada resultado se representará mediante un
registro inmutable con estos campos:

| Campo | Tipo en Python | Significado |
|---|---|---|
| `tipo_documento` | `str` | Tipo de identificación del paciente |
| `numero_documento` | `str` | Número de identificación del paciente |
| `id_laboratorio` | `str` | Laboratorio o IPS que produjo el resultado |
| `id_lote` | `str` | Lote de procesamiento del laboratorio |
| `fecha_resultado` | `datetime` | Fecha y hora del resultado |
| `indice_riesgo` | `int` | Índice de riesgo entre 0 y 100 |
| `municipio` | `str` | Municipio asociado al resultado |

La identidad de un paciente es la tupla
`(tipo_documento, numero_documento)`. No se usará solamente el número porque
dos documentos de distinto tipo podrían compartir la misma representación
textual. Los demás campos pertenecen al resultado clínico y no forman parte de
la clave.

La salida será una lista nueva con exactamente un resultado por clave de
paciente. Para facilitar la comparación reproducible entre estrategias, las
claves se presentarán en el orden de su primera aparición en la entrada. Los
registros de entrada son inmutables y ninguna estrategia puede alterar la
secuencia original.

#### Reglas de selección y desempate

Para cada paciente se conservará el registro cuya `fecha_resultado` sea más
reciente. Un registro reemplaza al guardado únicamente cuando su fecha es
estrictamente posterior. Si dos registros del mismo paciente tienen la misma
fecha y hora, se conserva el primero recibido en la secuencia de entrada. Esta
regla determinista evita que las estrategias escojan resultados diferentes en
un empate no especificado por el caso.

Una salida se considera correcta si cumple simultáneamente estas propiedades:

- contiene todas las claves de pacientes presentes en la entrada y ninguna
  adicional;
- contiene una sola vez cada clave;
- para cada clave conserva el resultado de fecha máxima;
- en un empate de fecha conserva el primero recibido;
- no modifica los registros ni el orden de la entrada;
- presenta la salida en el orden determinista definido.

La entrada vacía produce una lista vacía. Un paciente con un solo resultado se
conserva sin cambios. Los datos sintéticos usarán fechas comparables y un
índice de riesgo dentro del intervalo permitido, pero las estrategias no
supondrán que los resultados de un paciente llegan ordenados por fecha.

#### Estrategias que se compararán

1. **Búsqueda secuencial en una lista.** Representa el procedimiento actual:
   para cada resultado se recorre la lista consolidada hasta hallar la misma
   clave o llegar al final. Su peor caso es cuadrático y servirá como línea
   base.
2. **Ordenamiento estable.** Se agrupan los registros al ordenarlos por la
   clave del paciente y se elige el más reciente de cada grupo. La estabilidad
   preserva el primer registro recibido cuando las fechas empatan. Se espera
   un tiempo `Θ(n log n)`.
3. **Tabla hash con encadenamiento.** La clave del paciente se ubica en una
   cubeta y las colisiones se resuelven comparando la clave completa dentro de
   la lista de esa cubeta. Se controlará el factor de carga mediante
   redimensionamiento. Su tiempo esperado es lineal con un factor de carga
   acotado, aunque su peor caso sigue siendo cuadrático si todas las claves
   colisionan.

Las tres estrategias aplicarán las mismas reglas, recibirán las mismas entradas
y producirán los pacientes en el mismo orden de primera aparición. Las
mediciones incluirán todo el trabajo necesario para obtener esa salida, pero no
la generación previa de los datos de entrada.

### Diseño y complejidad de la consolidación

Para el análisis se usa `n` como la cantidad de resultados recibidos, `u` como
la cantidad de pacientes distintos, `m` como el número de cubetas de la tabla
hash y `α = u/m` como su factor de carga. La longitud de los documentos se
considera acotada por el formato del sistema; si se tratara como variable,
calcular y comparar claves añadiría un factor proporcional a esa longitud.

#### Estructuras de datos

| Elemento | Estructura | Motivo |
|---|---|---|
| Resultado | Clase de datos inmutable | Evita alterar los registros originales |
| Clave de paciente | Tupla `(tipo, número)` | Distingue documentos de diferente tipo |
| Estrategia secuencial | Lista de resultados | Representa el procedimiento actual |
| Estrategia de ordenamiento | Listas de pares `(posición, resultado)` | Conserva la primera aparición durante la agrupación |
| Estrategia hash | Arreglo de cubetas con listas | Permite resolver colisiones por encadenamiento |
| Orden de la tabla hash | Lista de claves | Produce la salida sin ordenar nuevamente |

La tabla hash implementada no depende de `dict`. Aplica una mezcla FNV-1a
determinista a los dos componentes de la clave y obtiene la cubeta mediante el
residuo con una capacidad prima. Cada búsqueda compara la clave completa, no
solo su valor hash. Antes de insertar un paciente nuevo, la tabla se amplía
cuando el factor de carga superaría `0,75`; la nueva capacidad es el primer
primo mayor o igual al doble de la anterior y todas las entradas se reubican.

#### Pseudocódigo de la búsqueda secuencial

```text
CONSOLIDAR-SECUENCIAL(resultados)
    consolidados ← lista vacía
    para cada resultado en resultados
        buscar su clave de izquierda a derecha en consolidados
        si la clave no existe
            agregar resultado al final
        si la clave existe y resultado.fecha > guardado.fecha
            reemplazar el guardado en la misma posición
    retornar consolidados
```

Con `u` pacientes ya consolidados, una inserción puede efectuar `u`
comparaciones. Si todas las claves son distintas, el total es
`0 + 1 + ... + (n - 1)`, por lo que el peor caso es `Θ(n²)`. Si todos los
resultados pertenecen al mismo paciente, la clave se encuentra en la primera
posición y el tiempo es `Θ(n)`. El espacio adicional de la salida es `Θ(u)`.

#### Pseudocódigo del ordenamiento estable

```text
CONSOLIDAR-ORDENAMIENTO(resultados)
    numerados ← pares (posición original, resultado)
    agrupados ← MERGE-SORT-ESTABLE(numerados, clave del paciente)
    seleccionados ← lista vacía
    para cada grupo de una misma clave en agrupados
        elegido ← primer resultado del grupo
        para cada candidato restante del grupo
            si candidato.fecha > elegido.fecha
                elegido ← candidato
        guardar (posición de la primera aparición, elegido)
    ordenar seleccionados por posición con MERGE-SORT-ESTABLE
    retornar los resultados sin las posiciones
```

El primer merge sort cuesta `Θ(n log n)`, recorrer los grupos cuesta `Θ(n)` y
el segundo ordenamiento cuesta `Θ(u log u)`. Como `u ≤ n`, el tiempo total es
`Θ(n log n)` y el espacio adicional máximo es `Θ(n)`. Dar prioridad a la mitad
izquierda durante la mezcla hace estable el ordenamiento; por eso, al reemplazar
solo ante una fecha estrictamente posterior, se conserva el primer registro en
los empates.

#### Pseudocódigo de la tabla hash

```text
CONSOLIDAR-HASH(resultados)
    tabla ← arreglo de cubetas vacías
    orden_claves ← lista vacía
    para cada resultado en resultados
        índice ← HASH(resultado.clave) módulo cantidad de cubetas
        buscar la clave completa dentro de esa cubeta
        si la clave existe y resultado.fecha > guardado.fecha
            reemplazar el resultado de esa entrada
        si la clave no existe
            redimensionar y reubicar entradas si se superaría α = 0,75
            agregar (clave, resultado) a su cubeta
            agregar clave a orden_claves
    retornar el resultado asociado con cada clave de orden_claves
```

Con dispersión uniforme, buscar o insertar cuesta `Θ(1 + α)` en promedio. Al
mantener `α` acotado, procesar y recuperar los resultados cuesta `Θ(n)`
esperado. Cada redimensionamiento cuesta `Θ(u)`, pero las capacidades crecen
aproximadamente al doble, de modo que ese trabajo es amortizado. En el peor
caso todas las claves caen en una misma cubeta y el tiempo se degrada a
`Θ(n²)`. El espacio es `Θ(m + u)` y, como el redimensionamiento mantiene
`m = Θ(u)`, se simplifica a `Θ(u)`.

#### Comparación teórica

| Estrategia | Mejor caso | Caso esperado o general | Peor caso | Espacio adicional |
|---|---:|---:|---:|---:|
| Búsqueda secuencial | `Θ(n)` | Depende de pacientes y orden | `Θ(n²)` | `Θ(u)` |
| Merge sort estable | `Θ(n log n)` | `Θ(n log n)` | `Θ(n log n)` | `Θ(n)` |
| Tabla hash | `Θ(n)` | `Θ(n)` con `α` acotado | `Θ(n²)` | `Θ(u)` |

La tabla hash es la candidata teórica para el volumen diario porque evita
ordenar y mantiene acceso esperado constante. Esta conclusión deberá
contrastarse con tiempo, operaciones y memoria medidos antes de formular la
recomendación definitiva.

### Evaluación experimental de la consolidación

Las tres estrategias recibieron exactamente las mismas entradas para cada
tamaño, generadas con una semilla fija y un 12 % de registros repetidos. Los
datos se crearon antes de iniciar el cronómetro. Cada tiempo es el promedio de
cinco ejecuciones con `time.perf_counter()` después de una ejecución de
calentamiento. La memoria adicional máxima se midió por separado con
`tracemalloc`; no incluye la entrada ya creada, el intérprete ni las
bibliotecas cargadas.

El contador registra comparaciones de claves, fechas y posiciones. Esta unidad
común permite estudiar el crecimiento con menos dependencia del computador,
aunque no representa todas las instrucciones ejecutadas: el tiempo sí incluye
el cálculo del hash, las asignaciones y los redimensionamientos. La estrategia
secuencial se midió hasta 4 000 resultados por su rápido crecimiento; merge
sort y hash se ampliaron hasta 100 000.

![Tiempo de consolidación](graficas/consolidacion_pacientes/tiempo_vs_n.png)

![Comparaciones de consolidación](graficas/consolidacion_pacientes/comparaciones_vs_n.png)

![Memoria de consolidación](graficas/consolidacion_pacientes/memoria_vs_n.png)

Algunos resultados representativos son:

| `n` | Estrategia | Tiempo promedio | Comparaciones | Memoria adicional máxima |
|---:|---|---:|---:|---:|
| 100 | Secuencial | 1,162 ms | 4 142 | 0,875 KiB |
| 100 | Merge sort | 0,577 ms | 1 118 | 5,305 KiB |
| 100 | Hash | 0,716 ms | 185 | 14,543 KiB |
| 4 000 | Secuencial | 1 781,823 ms | 6 754 891 | 28,805 KiB |
| 4 000 | Merge sort | 34,894 ms | 84 377 | 556,207 KiB |
| 4 000 | Hash | 26,807 ms | 7 621 | 776,871 KiB |
| 100 000 | Merge sort | 1 398,248 ms | 2 985 107 | 16 667,066 KiB |
| 100 000 | Hash | 985,473 ms | 184 250 | 26 309,043 KiB |

La búsqueda secuencial usa menos memoria porque su salida contiene referencias
a los registros sin estructuras auxiliares grandes, pero esa ventaja no
compensa su tiempo cuadrático. La tabla hash usa más memoria que merge sort en
estas mediciones debido al arreglo de cubetas, las listas de colisiones y la
lista que conserva el orden de primera aparición.

#### Factores de crecimiento observados

Para la búsqueda secuencial se compararon `n = 2 000` y `n = 4 000`. Al
duplicar la entrada, el tiempo se multiplicó por 4,05 y las comparaciones por
3,98, valores cercanos al factor 4 esperado para `Θ(n²)`. La memoria se
multiplicó por 2,03, coherente con almacenar una salida lineal.

Para las estrategias eficientes se compararon 50 000 y 100 000 resultados:

| Estrategia | Factor de tiempo | Factor de comparaciones | Factor de memoria | Referencia teórica |
|---|---:|---:|---:|---:|
| Merge sort | 2,23 | 2,14 | 1,98 | 2,13 para `n log n` |
| Hash | 2,25 | 2,01 | 2,01 | 2 para crecimiento lineal esperado |

Las comparaciones y la memoria siguen muy de cerca la teoría. Los factores de
tiempo son un poco mayores por el costo del intérprete, la gestión de memoria,
la caché y los procesos activos. Por eso la evidencia no se basa únicamente en
tiempos de pared.

#### Extrapolación al volumen diario

El volumen objetivo es `N = 1 450 000` resultados. La búsqueda secuencial se
proyectó desde 4 000 mediante `(N/4 000)²`; merge sort se proyectó desde
100 000 mediante `(N log N)/(100 000 log 100 000)`; y la tabla hash mediante
`N/100 000`. Para la memoria se aplicó crecimiento lineal a las tres.

| Estrategia | Factor aplicado al tiempo | Tiempo estimado | Comparaciones estimadas | Memoria adicional estimada |
|---|---:|---:|---:|---:|
| Secuencial | 131 406,25 | 65,04 horas | `8,88·10^11` | 10,20 MiB |
| Merge sort | 17,87 | 24,98 segundos | `5,33·10^7` | 236,01 MiB |
| Hash | 14,50 | 14,29 segundos | `2,67·10^6` | 372,54 MiB |

La estimación secuencial excede ampliamente la ventana nocturna de cuatro
horas. Merge sort y hash quedarían muy por debajo de ella para esta operación
aislada, y hash presenta el menor tiempo y número de comparaciones estimados.
Sin embargo, esto no demuestra todavía que el proceso completo cumpla la
ventana: las cuatro horas corresponden al conjunto de consolidación y lista de
llamadas, mientras que las siete horas actuales también son una cifra
combinada.

Estas proyecciones no son ejecuciones de 1 450 000 registros ni mediciones del
servidor de 380 W. Suponen que se mantiene el 12 % de repetidos, que no cambia
la distribución de las claves y que continúa la tendencia observada. El sistema
operativo, la versión de Python, la longitud real de los documentos, las
colisiones y otros procesos pueden modificar los tiempos y la memoria. Por
ello, los valores sirven para comparar órdenes de magnitud y deben validarse en
el servidor antes de una puesta en producción.

### Programación de las jornadas de las unidades móviles

Plataforma Pulso recibe mensualmente entre 40 y 120 solicitudes de jornada en
cada una de las nueve subregiones. Cada subregión dispone de una sola unidad
móvil. Una solicitud contiene la hora de inicio, la hora de finalización —que
ya incluye el desplazamiento— y el número de pacientes de alto riesgo
pendientes en el municipio.

La entrada de la operación es una lista de jornadas representadas por tuplas
`(inicio, fin, pacientes_alto_riesgo)`, con las horas expresadas en minutos. La
salida es un subconjunto de esas jornadas, ordenado por hora de inicio, cuya
suma de pacientes sea la mayor posible.

La solución debe cumplir las siguientes restricciones:

- una unidad móvil no puede estar asignada a dos jornadas que se crucen;
- dos jornadas que se tocan en un extremo son compatibles, pues se usa el
  intervalo `[inicio, fin)` y el desplazamiento ya está incluido en el fin;
- las solicitudes originales no se modifican;
- el resultado debe ser óptimo, no una aproximación;
- si existen varias programaciones con el mismo valor, cualquiera de ellas es
  válida siempre que cumpla las restricciones.

El criterio elegido es maximizar los pacientes de alto riesgo atendidos. No se
maximiza solamente la cantidad de jornadas, porque una jornada puede atender a
muchos más pacientes que otra.

### Supuestos de esta operación

- Cada subregión se procesa por separado porque dispone de una unidad móvil.
- La programación se calcula una vez al mes para cada una de las nueve
  subregiones.
- Dos jornadas que se tocan son compatibles: los intervalos son `[inicio, fin)`.
- El servidor consume 380 W durante la ejecución; se usa esa potencia constante
  como estimación conservadora.
- Los datos sintéticos conservan la estructura del caso, pero no representan
  una predicción de la demanda ni de los pacientes reales.

## Diseño de la solución

### Por qué el problema admite programación dinámica

Primero se ordenan las solicitudes por su hora de finalización. Para cada
jornada `j` se calcula `p(j)`: la cantidad de jornadas anteriores que terminan
antes o exactamente cuando empieza `j`. De esta manera, las jornadas
compatibles anteriores forman un prefijo de la lista ordenada.

Se define `M[j]` como el máximo número de pacientes que se puede atender usando
únicamente las primeras `j` jornadas. Para decidir sobre la jornada `j` se
comparan dos opciones:

1. No elegirla, por lo que se conserva `M[j - 1]`.
2. Elegirla, sumar sus pacientes `v[j]` y continuar con el mejor resultado del
   prefijo compatible `M[p(j)]`.

La recurrencia es:

```text
M[0] = 0
M[j] = max(M[j - 1], v[j] + M[p(j)])
```

El problema tiene **subestructura óptima**: si una solución óptima incluye la
jornada `j`, las jornadas anteriores seleccionadas deben formar una solución
óptima para el prefijo `p(j)`. Si no fuera así, se podría sustituir ese prefijo
por uno mejor y aumentar el total de pacientes, contradiciendo la optimalidad.

También existen **subproblemas traslapados**. Valores como `M[2]` o `M[3]`
pueden ser necesarios al evaluar distintas jornadas posteriores. La tabla
guarda cada resultado una sola vez y se llena de izquierda a derecha, ya que
`M[j]` depende únicamente de posiciones menores que `j`.

Ordenar y calcular `p(j)` mediante búsqueda binaria cuesta `Θ(n log n)`. Llenar
la tabla y reconstruir una solución cuesta `Θ(n)`. Por tanto, la complejidad
temporal total es `Θ(n log n)` y el espacio adicional es `Θ(n)`.

### Ejemplo resuelto a mano

Considérese una subregión con las siguientes seis solicitudes:

| Jornada | Horario | Pacientes |
|---|---|---:|
| A | 08:00–10:00 | 20 |
| B | 09:00–12:00 | 55 |
| C | 10:00–11:00 | 15 |
| D | 11:00–13:00 | 25 |
| E | 12:00–15:00 | 50 |
| F | 14:00–16:00 | 30 |

Al ordenar por hora de finalización se obtiene `A, C, B, D, E, F`. Los valores
de compatibilidad y de la tabla dinámica son:

| `j` | Jornada | `p(j)` | No elegir: `M[j-1]` | Elegir: `v[j] + M[p(j)]` | `M[j]` |
|---:|---|---:|---:|---:|---:|
| 0 | — | — | — | — | 0 |
| 1 | A | 0 | 0 | 20 + 0 = 20 | 20 |
| 2 | C | 1 | 20 | 15 + 20 = 35 | 35 |
| 3 | B | 0 | 35 | 55 + 0 = 55 | 55 |
| 4 | D | 2 | 55 | 25 + 35 = 60 | 60 |
| 5 | E | 3 | 60 | 50 + 55 = 105 | 105 |
| 6 | F | 4 | 105 | 30 + 60 = 90 | 105 |

La respuesta es `M[6] = 105`. Para reconstruirla se comienza en la última
posición. F no se elige porque 90 no supera 105. E sí se elige y se salta a
`p(5) = 3`. En esa posición se elige B y se llega al caso base. La programación
óptima es, por tanto, B de 09:00 a 12:00 y E de 12:00 a 15:00, que atienden
`55 + 50 = 105` pacientes sin cruces.

## Implementación

La solución se separó en módulos con responsabilidades específicas:

- [`estrategia.py`](src/jornadas_unidades/estrategia.py): ordenamiento,
  compatibilidades, tabla dinámica y reconstrucción de las jornadas.
- [`exhaustivo.py`](src/jornadas_unidades/exhaustivo.py): referencia exacta que
  enumera todos los subconjuntos para entradas pequeñas.
- [`regla_actual.py`](src/jornadas_unidades/regla_actual.py): asignación en el
  orden de llegada usada como línea base.
- [`datos.py`](src/jornadas_unidades/datos.py): solicitudes sintéticas con
  semilla fija.
- [`pruebas.py`](src/jornadas_unidades/pruebas.py): casos límite, ejemplo manual,
  contraejemplo y 50 instancias aleatorias.
- [`medicion.py`](src/jornadas_unidades/medicion.py): cronometraje, conteo de
  operaciones y generación de gráficas.

Las funciones trabajan con copias o listas nuevas para conservar las
solicitudes originales. La solución exhaustiva ordena una vez las solicitudes
y después recorre sus `2^n` subconjuntos; se usa como oráculo, no como propuesta
para producción.

## Evaluación del desempeño

### Complejidad y verificación

La programación dinámica tarda `Θ(n log n)`: el ordenamiento y las `n`
búsquedas binarias dominan el llenado y la reconstrucción lineales. Usa
`Θ(n)` de espacio para las listas ordenadas, las compatibilidades, la tabla y
la solución reconstruida.

La solución exhaustiva considera `2^n` subconjuntos y dedica hasta `Θ(n)` a
construir y revisar cada uno. Su tiempo es `Θ(n·2^n)` y su espacio auxiliar es
`Θ(n)`. La regla actual puede comparar cada nueva solicitud con todas las ya
aceptadas: tarda `O(n²)` en el peor caso y usa `O(n)` de espacio.

Para respaldar el análisis espacial se midió con `tracemalloc` la memoria
adicional máxima de la programación dinámica, después de generar la entrada y
de una ejecución inicial de calentamiento. Con 120 solicitudes el pico fue de
aproximadamente **5,6 KiB** y con 480 fue de **29,7 KiB**. Al multiplicar `n`
por cuatro, la memoria creció cerca de 5,3 veces, una variación compatible con
el crecimiento lineal y con la administración interna de memoria de Python.
La medición no incluye la lista de entrada, el intérprete ni sus bibliotecas;
representa solamente las asignaciones adicionales durante el algoritmo.

Las pruebas cubren la entrada vacía, una jornada, ninguna y todas las jornadas
cruzadas, jornadas que se tocan, el ejemplo manual y el contraejemplo de la
regla actual. También comparan el valor de la solución dinámica con el de la
exhaustiva en 50 instancias aleatorias pequeñas y verifican que no haya cruces.

### Metodología de medición

La comparación usa las mismas solicitudes para las tres estrategias en cada
tamaño. Las instancias se generan antes del cronómetro con la semilla
`2026 + n`; así, crear los datos no se atribuye a los algoritmos. Cada tiempo
es el promedio de cinco ejecuciones medido con `time.perf_counter()`.

La exhaustiva se ejecuta con 4, 6, 8, 10, 12 y 14 solicitudes. Las soluciones
prácticas también se miden con 20, 40, 80, 120, 240 y 480 solicitudes. El
experimento verifica que dinámica y exhaustiva produzcan el mismo valor óptimo.
Además se cuentan comparaciones, decisiones de la tabla y subconjuntos.

Los tiempos dependen del computador y de los procesos activos. Por eso se
interpretan junto con el conteo de operaciones, que permite comprobar la
tendencia con menor dependencia del equipo.

### Resultados y contraste con la teoría

![Tiempo frente al tamaño](graficas/jornadas_unidades/tiempo_vs_n.png)

![Operaciones frente al tamaño](graficas/jornadas_unidades/operaciones_vs_n.png)

La exhaustiva pasa de 16 subconjuntos con `n = 4` a 16 384 con `n = 14`; su
curva se separa rápidamente. Sirve para verificar entradas pequeñas, pero no
para las 40 a 120 solicitudes mensuales de una subregión.

La pareja común que duplica el tamaño es `n = 6` y `n = 12`. La dinámica pasó
de 23 a 71 operaciones (factor 3,09), la regla actual de 7 a 25 (factor 3,57)
y la exhaustiva de 64 a 4 096 subconjuntos (factor 64). El tiempo exhaustivo
pasó de 0,048 a 3,524 ms (factor 73,42). Su factor queda entre el conteo de
subconjuntos `2^n` y el costo total `n·2^n`, cuyo factor teórico es 128, porque
muchos subconjuntos con cruces se descartan antes de recorrerlos completos.
Los tiempos diminutos de las otras dos estrategias presentan mayor ruido, por
lo que también se analiza una duplicación con entradas grandes.

| `n` | Operaciones: dinámica | Operaciones: regla actual |
|---:|---:|---:|
| 40 | 359 | 327 |
| 80 | 858 | 1 536 |
| 120 | 1 446 | 2 863 |
| 240 | 3 344 | 10 954 |
| 480 | 7 649 | 42 917 |

Al duplicar de 240 a 480 solicitudes, las operaciones de la programación
dinámica se multiplicaron por `7 649 / 3 344 = 2,29` y su tiempo por cerca de
`0,346 / 0,161 = 2,15`. El factor teórico para `n log n` es aproximadamente
`2·log(480)/log(240) = 2,25`; los resultados son coherentes con esa tendencia.

En la regla actual, las operaciones se multiplicaron por 3,92 y el tiempo por
3,82. Ambos valores se aproximan al factor 4 de un crecimiento cuadrático. Las
diferencias restantes son normales por la distribución de cruces, las salidas
anticipadas y el ruido de medir fracciones de milisegundo.

La calidad del resultado también importa. En los datos sintéticos, la regla
actual dejó pacientes sin atender frente al óptimo:

| `n` | Pacientes: dinámica | Pacientes: regla actual | Diferencia |
|---:|---:|---:|---:|
| 40 | 2 201 | 1 736 | 465 |
| 80 | 4 116 | 3 902 | 214 |
| 120 | 5 171 | 3 778 | 1 393 |
| 480 | 21 933 | 16 576 | 5 357 |

Estas cifras no predicen la demanda real. Demuestran que aceptar por llegada
no garantiza el óptimo y que el resultado depende del orden de recepción.

### Escala real y ventana de referencia

El caso no fija una ventana para programar las jornadas. Se adopta como
referencia conservadora **un minuto para procesar las nueve subregiones**, pues
la planeación mensual debe responder de manera inmediata al coordinador. En la
ejecución usada para las gráficas se obtuvieron estos valores:

| `n` por subregión | Dinámica: 1 región | Regla actual: 1 región | Dinámica: 9 regiones |
|---:|---:|---:|---:|
| 40 | 0,028 ms | 0,042 ms | 0,252 ms |
| 120 | 0,079 ms | 0,288 ms | 0,711 ms |

Las dos soluciones prácticas caben en la referencia, pero solo la dinámica
garantiza el máximo de pacientes. Para la exhaustiva se tomó la medición de
15,1 ms con `n = 14` y se aplicó su crecimiento `n·2^n`. La estimación es de
unos 34 días por subregión con `n = 40` y `3,3·10^23` años con `n = 120`; por
tanto, no terminaría en una ventana útil. Son extrapolaciones, no ejecuciones
del volumen real.

## Análisis comparativo

### Contraejemplo de la asignación por orden de llegada

La Secretaría acepta las solicitudes en el orden en que llegan y rechaza las
que se crucen con una ya aceptada:

| Orden | Jornada | Inicio | Fin | Pacientes |
|---:|---|---:|---:|---:|
| 1 | A | 08:00 | 16:00 | 30 |
| 2 | B | 08:00 | 12:00 | 40 |
| 3 | C | 12:00 | 16:00 | 45 |

La regla acepta A y rechaza B y C, por lo que atiende 30 pacientes. La solución
óptima selecciona B y C, que son compatibles porque C empieza cuando B termina,
y atiende `40 + 45 = 85`. La regla actual deja de atender a **55 pacientes**.

### Condición que permitiría una estrategia voraz

Si el objetivo cambiara a maximizar solamente el **número de jornadas**, o si
todas tuvieran el mismo peso, sería correcta la selección de actividades:
ordenar por finalización y elegir siempre la siguiente jornada compatible que
termine primero. Esto no vuelve óptimo el orden de llegada, porque la estrategia
voraz correcta necesita ordenar previamente.

### Recomendación para la operación

Se recomienda la programación dinámica de intervalos ponderados. Garantiza el
máximo de pacientes sin cruces, conserva las entradas y escala como
`Θ(n log n)`. La exhaustiva debe limitarse a pruebas pequeñas y la regla actual
puede conservarse como línea base, pero no debe decidir la programación.

El principal riesgo es la calidad de los datos: horarios o cantidades de
pacientes incorrectos producen una programación óptima para una entrada
equivocada. La organización debe validar las solicitudes y conservar su
trazabilidad. Si el volumen crece, la solución dinámica mantiene una tendencia
muy inferior al crecimiento cuadrático observado en la regla actual.

## Implicaciones éticas, sociales y ambientales

### Consumo energético

Se estima la energía con `E = P·t`, donde `P = 380 W = 0,38 kW` y el tiempo se
convierte de segundos a horas. La proyección anual considera nueve subregiones,
una ejecución mensual por subregión y doce meses.

| `n` | Energía anual: dinámica | Energía anual: regla actual | Ahorro anual estimado |
|---:|---:|---:|---:|
| 40 | `3,19·10^-7` kWh | `4,79·10^-7` kWh | `1,60·10^-7` kWh |
| 120 | `9,01·10^-7` kWh | `3,28·10^-6` kWh | `2,38·10^-6` kWh |

El ahorro absoluto es muy pequeño porque esta operación dura milisegundos y se
ejecuta solo una vez al mes. No sería responsable afirmar un gran beneficio
ambiental con estas cifras. La ventaja principal es social y operativa: atender
el máximo de pacientes de alto riesgo con un costo computacional bajo.

La estimación supone 380 W constantes durante el algoritmo y no incluye el
consumo en reposo, refrigeración, almacenamiento ni otros procesos del servidor.
La exhaustiva, en cambio, requeriría cerca de 306 kWh para una sola subregión de
40 solicitudes y sería físicamente inviable con 120. Evitarla sí previene un
desperdicio energético considerable.

Las demás implicaciones éticas, sociales, normativas y ambientales del proceso
completo quedan pendientes para la entrega final del proyecto.

## Conclusiones

La programación dinámica coincide con la solución exacta en las pruebas y
supera la regla actual en pacientes atendidos. Las mediciones reproducen el
crecimiento `Θ(n log n)` y muestran que el volumen real cabe ampliamente en la
referencia operativa. La solución exhaustiva es útil para verificar, no para
producción. Las conclusiones del proceso completo se completarán con la segunda
operación en la entrega final.

## Reproducción de pruebas y mediciones

Desde la raíz del repositorio, cree y active el entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Ejecute las pruebas y luego regenere las mediciones y gráficas:

```bash
python src/jornadas_unidades/pruebas.py
python src/jornadas_unidades/medicion.py
```

La medición usa semillas y tamaños fijos. Los tiempos pueden variar entre
equipos, pero las instancias, los conteos y las tendencias son reproducibles.

