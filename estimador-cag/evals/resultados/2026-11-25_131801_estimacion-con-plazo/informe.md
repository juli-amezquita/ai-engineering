# Consistencia: estimacion-con-plazo

- Transcripción: `transcripciones/onboarding_seguridad_canteras.txt` (huella 402c1ff99f4f)
- Cambios de alcance: no
- Recorrido: inventario · modelo: claude-haiku-5-5 · system prompt 3b479127cf2c · commit 96aef76 con cambios sin commit en app/
- Fecha: 2026-11-25T13:18:01
- Llamadas válidas: 6 de 10 · costo total 0.0598 USD

## Cifras

| | Media | Mediana | Mínimo | Máximo | Amplitud | CV |
|---|---:|---:|---:|---:|---:|---:|
| Horas base | 1,797 | 1,795 | 1,675 | 1,886 | 13 % | 5 % |
| Precio (USD) | 262,623 | 263,841 | 246,461 | 276,492 | 12 % | 4 % |
| Semanas | 17 | 17 | 17 | 17 | 0 % | 0 % |

La amplitud dice cuánto más alta es la llamada más alta que la más baja. El CV (coeficiente de variación) es la desviación estándar dividida por la media: cuanto más bajo, más estable. La mediana es la cifra que daría quedarse con la llamada del medio.

## Dónde está la variación: horas base por perfil

Ordenados de más a menos variación. Si un perfil no aparece en una llamada, cuenta como 0 horas.

| Perfil | Llamadas en las que aparece | Media | Mínimo | Máximo | Desviación estándar |
|---|---:|---:|---:|---:|---:|
| Backend | 6 de 6 | 342 | 299 | 406 | 37 |
| Frontend | 6 de 6 | 271 | 252 | 287 | 13 |
| Full-stack | 1 de 6 | 4 | 0 | 24 | 10 |
| Diseño UX/UI | 6 de 6 | 238 | 227 | 247 | 7 |
| Liderazgo técnico | 6 de 6 | 216 | 203 | 225 | 7 |
| QA | 6 de 6 | 197 | 187 | 206 | 7 |
| Ingeniería de datos | 6 de 6 | 115 | 108 | 122 | 6 |
| Consultoría de RR. HH. | 6 de 6 | 91 | 86 | 98 | 6 |
| Ciencia de datos | 6 de 6 | 15 | 8 | 22 | 5 |
| Gestión de proyecto | 6 de 6 | 113 | 108 | 117 | 4 |
| DevOps | 6 de 6 | 82 | 78 | 86 | 3 |
| IA / ML | 6 de 6 | 111 | 111 | 111 | 0 |

## Cada llamada

| Llamada | Horas base | Precio (USD) | Semanas (propuestas) | Plazo pedido | Tareas | Puntos por confirmar | Etapas alargadas por Python |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,880 | 268,633 | 17 (17) | 17 | 14 | 2 | 0 |
| 2 | 1,886 | 276,492 | 17 (17) | 17 | 15 | 2 | 0 |
| 5 | 1,834 | 268,849 | 17 (17) | 17 | 15 | 2 | 0 |
| 8 | 1,675 | 246,461 | 17 (17) | 17 | 13 | 2 | 0 |
| 9 | 1,749 | 256,256 | 17 (17) | 17 | 15 | 2 | 0 |
| 10 | 1,756 | 259,049 | 17 (17) | 17 | 14 | 3 | 0 |

## Puntos de alcance por confirmar

En el recorrido directo los redacta el modelo, así que el mismo punto puede salir con palabras distintas: hay que leerlos para ver si coinciden. Con el inventario, son los requisitos opcionales o condicionados, con la descripción que les dio el modelo.

**Llamada 1**
- Formación de usuarios y acompañamiento del piloto en dos canteras antes del despliegue: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 2**
- Piloto de la app en dos canteras antes del despliegue completo, con formación de usuarios y acompañamiento en sede: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 5**
- Piloto de la app en dos canteras antes del despliegue general: se mencionó como deseable, sin decidirlo.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 8**
- Piloto de la app de incorporación en dos canteras antes del despliegue completo: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

**Llamada 9**
- Lectura de datos de personas desde el HRIS por API: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas: se mencionó como deseable, sin decidirlo.

**Llamada 10**
- Conexión con el HRIS por API para leer las personas y su estructura: depende de algo que la reunión no decidió.
- Piloto de la app en dos canteras antes del despliegue en todas: depende de algo que la reunión no decidió.
- Formación de riesgos del lugar para contratistas que entran a las canteras: se mencionó como deseable, sin decidirlo.

## Llamadas que fallaron

- Llamada 3: ReadTimeout: 
- Llamada 4: ReadTimeout: 
- Llamada 6: ReadTimeout: 
- Llamada 7: ReadTimeout: 
