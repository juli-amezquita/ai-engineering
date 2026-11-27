# Consistencia: estimacion-calibrada

- Transcripción: `transcripciones/onboarding_seguridad_canteras.txt` (huella 402c1ff99f4f)
- Cambios de alcance: no
- Recorrido: inventario · modelo: claude-haiku-5-5 · system prompt 515abb70a2e0 · commit 96aef76 con cambios sin commit en app/
- Fecha: 2026-11-24T22:29:51
- Llamadas válidas: 10 de 10 · costo total 0.1008 USD

## Cifras

| | Media | Mediana | Mínimo | Máximo | Amplitud | CV |
|---|---:|---:|---:|---:|---:|---:|
| Horas base | 1,836 | 1,826 | 1,733 | 2,018 | 16 % | 5 % |
| Precio (USD) | 268,623 | 266,722 | 252,798 | 299,193 | 18 % | 5 % |
| Semanas | 17 | 17 | 13 | 23 | 77 % | 15 % |

La amplitud dice cuánto más alta es la llamada más alta que la más baja. El CV (coeficiente de variación) es la desviación estándar dividida por la media: cuanto más bajo, más estable. La mediana es la cifra que daría quedarse con la llamada del medio.

## Dónde está la variación: horas base por perfil

Ordenados de más a menos variación. Si un perfil no aparece en una llamada, cuenta como 0 horas.

| Perfil | Llamadas en las que aparece | Media | Mínimo | Máximo | Desviación estándar |
|---|---:|---:|---:|---:|---:|
| Backend | 10 de 10 | 356 | 316 | 508 | 61 |
| Full-stack | 2 de 10 | 8 | 0 | 44 | 16 |
| Frontend | 10 de 10 | 271 | 255 | 295 | 13 |
| Consultoría de RR. HH. | 10 de 10 | 93 | 86 | 121 | 11 |
| Liderazgo técnico | 10 de 10 | 221 | 208 | 244 | 11 |
| QA | 10 de 10 | 199 | 190 | 216 | 8 |
| Ingeniería de datos | 10 de 10 | 120 | 112 | 132 | 7 |
| Ciencia de datos | 9 de 10 | 14 | 0 | 24 | 7 |
| Gestión de proyecto | 10 de 10 | 118 | 109 | 128 | 7 |
| Diseño UX/UI | 10 de 10 | 241 | 233 | 250 | 6 |
| DevOps | 10 de 10 | 84 | 80 | 91 | 4 |
| IA / ML | 10 de 10 | 111 | 111 | 111 | 0 |

## Cada llamada

| Llamada | Horas base | Precio (USD) | Semanas (propuestas) | Tareas | Puntos por confirmar | Etapas alargadas por Python |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,743 | 258,101 | 18 (18) | 14 | 2 | 0 |
| 2 | 2,018 | 299,193 | 23 (20) | 15 | 2 | 1 |
| 3 | 1,733 | 252,798 | 13 (13) | 14 | 3 | 0 |
| 4 | 1,897 | 276,360 | 18 (18) | 15 | 2 | 0 |
| 5 | 1,893 | 272,844 | 15 (15) | 15 | 3 | 0 |
| 6 | 1,899 | 273,166 | 17 (17) | 15 | 2 | 0 |
| 7 | 1,741 | 257,066 | 16 (16) | 14 | 2 | 0 |
| 8 | 1,778 | 258,268 | 17 (17) | 14 | 2 | 0 |
| 9 | 1,789 | 260,600 | 17 (17) | 14 | 1 | 0 |
| 10 | 1,864 | 277,836 | 16 (16) | 15 | 2 | 0 |

## Puntos de alcance por confirmar

En el recorrido directo los redacta el modelo, así que el mismo punto puede salir con palabras distintas: hay que leerlos para ver si coinciden. Con el inventario, son los requisitos opcionales o condicionados, con la descripción que les dio el modelo.

**Llamada 1**
- Formación de riesgos del lugar para contratistas que entran a las canteras, como un curso aparte: se mencionó como deseable, sin decidirlo.
- Piloto en dos canteras antes de desplegar en todas: depende de algo que la reunión no decidió.

**Llamada 2**
- Piloto de la app en dos canteras antes de desplegar en todas: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras, como módulo adicional: se mencionó como deseable, sin decidirlo.

**Llamada 3**
- Lectura de empleados y fechas de alta y baja desde el HRIS existente para calcular la rotación: depende de algo que la reunión no decidió.
- Piloto en dos canteras con formación de usuarios y preparación del despliegue: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para los contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 4**
- Curso corto de formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
- Piloto de la app de incorporación en dos canteras, con formación a los usuarios y acompañamiento en sus sedes antes del despliegue: depende de algo que la reunión no decidió.

**Llamada 5**
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
- Lectura de empleados desde el sistema de RR. HH. con API para cruzar la rotación y la plantilla: depende de algo que la reunión no decidió.
- Piloto de la solución en dos canteras antes de desplegar en las demás: depende de algo que la reunión no decidió.

**Llamada 6**
- Piloto de la app en dos canteras con acompañamiento a los supervisores y preparación del despliegue: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 7**
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
- Piloto en dos canteras antes de desplegar en todas: depende de algo que la reunión no decidió.

**Llamada 8**
- Piloto en dos canteras con acompañamiento para formar a los usuarios y preparar el despliegue: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 9**
- Formación de riesgos del lugar para contratistas que entran a las canteras, si se incluye: se mencionó como deseable, sin decidirlo.

**Llamada 10**
- Lectura de empleados del HRIS para asignar cantera y supervisor en el cruce de rotación: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
