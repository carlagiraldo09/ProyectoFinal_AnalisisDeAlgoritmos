# Proyecto final — Análisis de algoritmos

Repositorio del equipo para el Caso 2: Plataforma Pulso.

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

