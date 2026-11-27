# Consistencia: estimacion-con-plazo

- Transcripción: `transcripciones/onboarding_seguridad_canteras.txt` (huella 402c1ff99f4f)
- Cambios de alcance: no
- Recorrido: inventario · modelo: claude-haiku-5-5 · system prompt 3b479127cf2c · commit 96aef76 con cambios sin commit en app/
- Fecha: 2026-11-25T13:32:36
- Llamadas válidas: 10 de 10 · costo total 0.1030 USD

## Cifras

| | Media | Mediana | Mínimo | Máximo | Amplitud | CV |
|---|---:|---:|---:|---:|---:|---:|
| Horas base | 1,832 | 1,792 | 1,725 | 2,077 | 20 % | 6 % |
| Precio (USD) | 268,506 | 263,044 | 253,801 | 311,052 | 23 % | 6 % |
| Semanas | 17 | 17 | 17 | 17 | 0 % | 0 % |

La amplitud dice cuánto más alta es la llamada más alta que la más baja. El CV (coeficiente de variación) es la desviación estándar dividida por la media: cuanto más bajo, más estable. La mediana es la cifra que daría quedarse con la llamada del medio.

## Dónde está la variación: horas base por perfil

Ordenados de más a menos variación. Si un perfil no aparece en una llamada, cuenta como 0 horas.

| Perfil | Llamadas en las que aparece | Media | Mínimo | Máximo | Desviación estándar |
|---|---:|---:|---:|---:|---:|
| Backend | 10 de 10 | 350 | 310 | 420 | 29 |
| QA | 10 de 10 | 196 | 182 | 246 | 19 |
| Ingeniería de datos | 10 de 10 | 123 | 108 | 171 | 19 |
| IA / ML | 10 de 10 | 116 | 111 | 166 | 17 |
| Frontend | 10 de 10 | 280 | 261 | 295 | 10 |
| Gestión de proyecto | 10 de 10 | 116 | 109 | 139 | 10 |
| Liderazgo técnico | 10 de 10 | 217 | 208 | 242 | 10 |
| Consultoría de RR. HH. | 10 de 10 | 91 | 86 | 109 | 8 |
| Ciencia de datos | 10 de 10 | 15 | 8 | 24 | 5 |
| Diseño UX/UI | 10 de 10 | 243 | 235 | 249 | 4 |
| DevOps | 10 de 10 | 84 | 80 | 93 | 4 |

## Cada llamada

| Llamada | Horas base | Precio (USD) | Semanas (propuestas) | Plazo pedido | Tareas | Puntos por confirmar | Etapas alargadas por Python |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,786 | 262,665 | 17 (17) | 17 | 15 | 3 | 0 |
| 2 | 1,763 | 256,789 | 17 (17) | 17 | 15 | 3 | 0 |
| 3 | 1,797 | 263,423 | 17 (17) | 17 | 14 | 3 | 0 |
| 4 | 1,810 | 264,325 | 17 (17) | 17 | 14 | 3 | 0 |
| 5 | 1,937 | 283,443 | 17 (17) | 17 | 15 | 2 | 0 |
| 6 | 1,780 | 258,010 | 17 (17) | 17 | 14 | 2 | 0 |
| 7 | 1,783 | 259,082 | 17 (17) | 17 | 14 | 3 | 0 |
| 8 | 1,861 | 272,470 | 17 (17) | 17 | 14 | 3 | 0 |
| 9 | 2,077 | 311,052 | 17 (17) | 17 | 14 | 3 | 0 |
| 10 | 1,725 | 253,801 | 17 (17) | 17 | 14 | 3 | 0 |

## Puntos de alcance por confirmar

En el recorrido directo los redacta el modelo, así que el mismo punto puede salir con palabras distintas: hay que leerlos para ver si coinciden. Con el inventario, son los requisitos opcionales o condicionados, con la descripción que les dio el modelo.

**Llamada 1**
- Lectura de datos de empleados desde el HRIS de la empresa, que tiene API: depende de algo que la reunión no decidió.
- Piloto de incorporación en dos canteras antes del despliegue completo: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 2**
- Lectura del HRIS para obtener empleados y su historial de cambios: depende de algo que la reunión no decidió.
- Formación a usuarios y acompañamiento de un piloto en dos canteras: depende de algo que la reunión no decidió.
- Módulos de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 3**
- Lectura de la plantilla desde el HRIS por API, si se decide conectarlo: depende de algo que la reunión no decidió.
- Piloto en dos canteras con formación de usuarios y acompañamiento de la implantación: depende de algo que la reunión no decidió.
- Módulo de formación de riesgos del lugar para contratistas: se mencionó como deseable, sin decidirlo.

**Llamada 4**
- Lectura de datos de empleados y rotación desde el HRIS con API, para el cruce: depende de algo que la reunión no decidió.
- Piloto en dos canteras y preparación del despliegue en la temporada: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 5**
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
- Piloto en dos canteras con formación de usuarios y acompañamiento: depende de algo que la reunión no decidió.

**Llamada 6**
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
- Acompañamiento de un piloto en dos canteras, con formación de usuarios y preparación del despliegue: se mencionó como deseable, sin decidirlo.

**Llamada 7**
- Lectura de empleados desde el HRIS existente, que tiene API, para la rotación: depende de algo que la reunión no decidió.
- Piloto de la app en dos canteras antes del despliegue general: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 8**
- Conexión con el sistema de RR. HH. que tiene API, para leer los datos de personas: depende de algo que la reunión no decidió.
- Piloto en dos canteras con formación de usuarios y preparación del despliegue: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 9**
- Lectura de empleados y estructura por cantera y supervisor desde el HRIS de la empresa, si se confirma su conexión: depende de algo que la reunión no decidió.
- Piloto en dos canteras con acompañamiento en sus sedes y preparación del despliegue: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 10**
- Lectura de datos de empleados y supervisores desde el HRIS actual por su API: depende de algo que la reunión no decidió.
- Piloto en dos canteras antes de desplegar en todas: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.
