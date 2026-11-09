# Proyecto final — Análisis de algoritmos

Repositorio del equipo para el Caso 2: Plataforma Pulso.

## Análisis del problema

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

## Análisis comparativo

### Contraejemplo de la asignación por orden de llegada

La Secretaría acepta actualmente las solicitudes en el orden en que llegan y
rechaza cada solicitud que se cruce con una jornada aceptada previamente. El
siguiente ejemplo muestra que esa regla puede dejar sin atención a muchos
pacientes de alto riesgo:

| Orden de llegada | Jornada | Inicio | Fin | Pacientes de alto riesgo |
|---:|---|---:|---:|---:|
| 1 | A | 08:00 | 16:00 | 30 |
| 2 | B | 08:00 | 12:00 | 40 |
| 3 | C | 12:00 | 16:00 | 45 |

Se supone que las jornadas usan intervalos de la forma `[inicio, fin)`. Por
eso, B y C son compatibles: C empieza exactamente cuando B termina.

La regla actual recibe primero A y la acepta. Después rechaza B y C porque
ambas se cruzan con A. Su programación atiende, por tanto, **30 pacientes**.

La solución óptima descarta A y selecciona B y C. Estas jornadas no se cruzan
y atienden en total:

```text
40 + 45 = 85 pacientes
```

La asignación por orden de llegada deja de atender a **55 pacientes de alto
riesgo** frente al óptimo. El problema no depende solamente de encontrar
horarios disponibles: también debe considerar el peso de cada solicitud, que
en este caso es la cantidad de pacientes pendientes.

### Condición que permitiría una estrategia voraz

La programación dinámica es necesaria porque el objetivo elegido es maximizar
la suma de pacientes atendidos y cada jornada puede tener un peso diferente.
Elegir una jornada que termina temprano no garantiza conservar la combinación
con mayor peso total.

Si la Secretaría cambiara el objetivo para maximizar únicamente el **número de
jornadas**, sin importar cuántos pacientes atiende cada una, se podría aplicar
la estrategia voraz de selección de actividades: ordenar por hora de
finalización y aceptar siempre la siguiente jornada compatible que termine
primero. La misma estrategia también sería suficiente si todas las jornadas
tuvieran exactamente el mismo peso.

Este cambio no haría óptima la asignación por orden de llegada. La regla voraz
correcta requiere ordenar primero las solicitudes por su hora de finalización.

### Metodología de medición

La comparación usa las mismas solicitudes para las tres estrategias en cada
tamaño. Las instancias se generan antes de iniciar el cronómetro con la semilla
reproducible `2026 + n`; así, el costo de crear los datos no se atribuye a los
algoritmos. Cada tiempo corresponde al promedio de cinco ejecuciones.

La solución exhaustiva se ejecuta solamente entre 4 y 14 solicitudes, porque
examina los `2^n` subconjuntos. En esos tamaños se verifica automáticamente que
su total de pacientes coincida con el de programación dinámica. Las dos
estrategias prácticas también se miden con 20, 40, 80, 120, 240 y 480
solicitudes. Además del tiempo, se cuentan operaciones representativas:
comparaciones del ordenamiento, búsquedas binarias y decisiones de la tabla
para programación dinámica, y comparaciones de cruces para la regla actual.

Los tiempos dependen del equipo y de los procesos activos, por lo que no deben
interpretarse de forma aislada. El conteo de operaciones y la forma de las
curvas permiten comprobar la tendencia con menos dependencia del computador.

### Resultados

![Tiempo frente al tamaño](graficas/jornadas_unidades/tiempo_vs_n.png)

![Operaciones frente al tamaño](graficas/jornadas_unidades/operaciones_vs_n.png)

La estrategia exhaustiva evidencia el crecimiento exponencial: pasa de 16
subconjuntos con `n = 4` a 16 384 con `n = 14`. En la gráfica de tiempo se
separa rápidamente de las otras soluciones. Aunque sirve como oráculo para
verificar instancias pequeñas, no es viable para las 40 a 120 solicitudes
mensuales de una subregión.

La siguiente selección de los conteos muestra el comportamiento de las dos
alternativas que sí pueden procesar entradas grandes:

| Solicitudes `n` | Operaciones de programación dinámica | Operaciones de la regla actual |
|---:|---:|---:|
| 40 | 359 | 327 |
| 80 | 858 | 1 536 |
| 120 | 1 446 | 2 863 |
| 240 | 3 344 | 10 954 |
| 480 | 7 649 | 42 917 |

La programación dinámica sigue la tendencia esperada de `Θ(n log n)`, causada
por el ordenamiento y las búsquedas binarias. La regla por orden de llegada
puede hacer pocas comparaciones en algunas instancias, pero en el peor caso
compara cada solicitud con muchas jornadas aceptadas y alcanza `O(n²)`. En la
instancia de 480 solicitudes hizo más de cinco veces las operaciones de la
solución dinámica. La curva de tiempo reproduce esta diferencia y muestra que
la solución dinámica escala mejor.

El costo computacional no es el único criterio. En las instancias sintéticas,
la regla actual también dejó pacientes sin atender frente al óptimo:

| `n` | Pacientes: dinámica | Pacientes: regla actual | Diferencia |
|---:|---:|---:|---:|
| 40 | 2 201 | 1 736 | 465 |
| 80 | 4 116 | 3 902 | 214 |
| 120 | 5 171 | 3 778 | 1 393 |
| 480 | 21 933 | 16 576 | 5 357 |

Estos valores no predicen la demanda real, porque provienen de datos
sintéticos. Sí demuestran que aceptar por llegada no ofrece garantía de
optimalidad y que su resultado depende del orden en que se reciben las
solicitudes.

### Recomendación para la operación

Se recomienda reemplazar la asignación por orden de llegada con la solución de
programación dinámica de intervalos ponderados. Es la única de las estrategias
prácticas evaluadas que garantiza maximizar los pacientes de alto riesgo sin
asignar jornadas cruzadas. Su costo `Θ(n log n)` es adecuado para el volumen
mensual indicado por Plataforma Pulso y, en las pruebas, se mantuvo por debajo
de un milisegundo incluso con 480 solicitudes.

La estrategia exhaustiva debe conservarse únicamente para pruebas automáticas
con entradas pequeñas. La regla actual puede mantenerse como línea base de
comparación, pero no debe decidir la programación, pues no garantiza la mejor
cobertura y su costo puede crecer cuadráticamente.

