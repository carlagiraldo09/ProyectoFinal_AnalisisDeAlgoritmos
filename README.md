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

