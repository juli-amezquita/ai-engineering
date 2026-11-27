# Consistencia: estimacion-con-inventario

- Transcripción: `transcripciones/onboarding_seguridad_canteras.txt` (huella 402c1ff99f4f)
- Cambios de alcance: no
- Recorrido: inventario · modelo: claude-haiku-5-5 · system prompt 7f22312e0b1b · commit 96aef76 con cambios sin commit en app/
- Fecha: 2026-11-24T20:49:55
- Llamadas válidas: 10 de 10 · costo total 0.1019 USD

## Cifras

| | Media | Mediana | Mínimo | Máximo | Amplitud | CV |
|---|---:|---:|---:|---:|---:|---:|
| Horas base | 1,900 | 1,879 | 1,803 | 2,060 | 14 % | 4 % |
| Precio (USD) | 223,340 | 221,882 | 209,896 | 242,562 | 16 % | 5 % |
| Semanas | 18 | 18 | 16 | 21 | 31 % | 8 % |

La amplitud dice cuánto más alta es la llamada más alta que la más baja. El CV (coeficiente de variación) es la desviación estándar dividida por la media: cuanto más bajo, más estable. La mediana es la cifra que daría quedarse con la llamada del medio.

## Dónde está la variación: horas base por perfil

Ordenados de más a menos variación. Si un perfil no aparece en una llamada, cuenta como 0 horas.

| Perfil | Llamadas en las que aparece | Media | Mínimo | Máximo | Desviación estándar |
|---|---:|---:|---:|---:|---:|
| Backend | 10 de 10 | 62 | 18 | 106 | 28 |
| Full-stack | 10 de 10 | 453 | 434 | 496 | 22 |
| QA | 10 de 10 | 470 | 434 | 508 | 20 |
| Ingeniería de datos | 10 de 10 | 122 | 92 | 152 | 20 |
| Frontend | 10 de 10 | 27 | 8 | 58 | 15 |
| Consultoría de RR. HH. | 10 de 10 | 101 | 86 | 134 | 15 |
| Gestión de proyecto | 10 de 10 | 200 | 189 | 227 | 13 |
| Diseño UX/UI | 10 de 10 | 248 | 235 | 261 | 9 |
| Ciencia de datos | 8 de 10 | 14 | 0 | 24 | 8 |
| Liderazgo técnico | 10 de 10 | 72 | 71 | 76 | 2 |
| IA / ML | 10 de 10 | 111 | 111 | 111 | 0 |
| DevOps | 10 de 10 | 20 | 20 | 20 | 0 |

## Cada llamada

| Llamada | Horas base | Precio (USD) | Semanas (propuestas) | Tareas | Puntos por confirmar | Etapas alargadas por Python |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,817 | 215,791 | 19 (16) | 14 | 3 | 1 |
| 2 | 1,933 | 227,154 | 16 (16) | 15 | 2 | 0 |
| 3 | 1,909 | 226,411 | 18 (18) | 14 | 1 | 0 |
| 4 | 2,019 | 242,562 | 21 (21) | 15 | 2 | 0 |
| 5 | 1,860 | 218,692 | 19 (19) | 15 | 2 | 0 |
| 6 | 1,898 | 222,399 | 19 (17) | 14 | 3 | 1 |
| 7 | 2,060 | 237,365 | 18 (18) | 16 | 2 | 0 |
| 8 | 1,849 | 221,366 | 18 (16) | 13 | 2 | 1 |
| 9 | 1,852 | 211,767 | 18 (18) | 14 | 3 | 0 |
| 10 | 1,803 | 209,896 | 16 (16) | 13 | 2 | 0 |

## Puntos de alcance por confirmar

En el recorrido directo los redacta el modelo, así que el mismo punto puede salir con palabras distintas: hay que leerlos para ver si coinciden. Con el inventario, son los requisitos opcionales o condicionados, con la descripción que les dio el modelo.

**Llamada 1**
- Lectura de datos de empleados desde el HRIS de la empresa a través de su API: depende de algo que la reunión no decidió.
- Acompañamiento de la formación de supervisores y del piloto en dos canteras: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 2**
- Acompañamiento de un piloto en dos canteras y preparación del despliegue: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras, con los mismos módulos: se mencionó como deseable, sin decidirlo.

**Llamada 3**
- Piloto en dos canteras con formación de usuarios y acompañamiento en sedes: depende de algo que la reunión no decidió.

**Llamada 4**
- Conexión con el HRIS de la empresa para leer los datos de empleados, según lo que se decida: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 5**
- Lectura de empleados, cantera y supervisor desde el HRIS con API: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 6**
- Conexión con el HRIS para leer los datos de empleados: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
- Piloto en dos canteras con formación a usuarios y acompañamiento en sedes: depende de algo que la reunión no decidió.

**Llamada 7**
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
- Piloto inicial en dos canteras con formación a usuarios y acompañamiento en sus sedes: depende de algo que la reunión no decidió.

**Llamada 8**
- Conexión con el HRIS de la empresa para leer datos de empleados y así calcular la rotación: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras, dentro de la misma app: se mencionó como deseable, sin decidirlo.

**Llamada 9**
- Lectura de datos de empleados del HRIS para alimentar la aplicación y el cruce de rotación: depende de algo que la reunión no decidió.
- Piloto en dos canteras con formación a usuarios, acompañamiento en las sedes y preparación del despliegue: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 10**
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
- Piloto en dos canteras antes de la próxima temporada de contratación: depende de algo que la reunión no decidió.
