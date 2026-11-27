# Consistencia: linea-base

- Transcripción: `transcripciones/onboarding_seguridad_canteras.txt` (huella 402c1ff99f4f)
- Cambios de alcance: no
- Recorrido: directo · modelo: claude-haiku-5-5 · system prompt d574f47c2064 · commit 88c961b
- Fecha: 2026-11-24T18:29:34
- Llamadas válidas: 5 de 5 · costo total 0.0401 USD

## Cifras

| | Media | Mediana | Mínimo | Máximo | Amplitud | CV |
|---|---:|---:|---:|---:|---:|---:|
| Horas base | 1,879 | 1,848 | 1,640 | 2,200 | 34 % | 11 % |
| Precio (USD) | 282,564 | 278,681 | 260,289 | 315,561 | 21 % | 7 % |
| Semanas | 16 | 16 | 16 | 17 | 6 % | 3 % |

La amplitud dice cuánto más alta es la llamada más alta que la más baja. El CV (coeficiente de variación) es la desviación estándar dividida por la media: cuanto más bajo, más estable. La mediana es la cifra que daría quedarse con la llamada del medio.

## Dónde está la variación: horas base por perfil

Ordenados de más a menos variación. Si un perfil no aparece en una llamada, cuenta como 0 horas.

| Perfil | Llamadas en las que aparece | Media | Mínimo | Máximo | Desviación estándar |
|---|---:|---:|---:|---:|---:|
| Móvil | 3 de 5 | 211 | 0 | 368 | 193 |
| Backend | 5 de 5 | 292 | 224 | 404 | 77 |
| Frontend | 5 de 5 | 165 | 96 | 288 | 73 |
| Full-stack | 2 de 5 | 43 | 0 | 120 | 60 |
| Consultoría de RR. HH. | 5 de 5 | 130 | 56 | 176 | 45 |
| QA | 5 de 5 | 160 | 120 | 200 | 33 |
| IA / ML | 5 de 5 | 246 | 200 | 288 | 33 |
| Ingeniería de datos | 4 de 5 | 48 | 0 | 80 | 31 |
| Ciencia de datos | 4 de 5 | 43 | 0 | 80 | 29 |
| Diseño UX/UI | 5 de 5 | 137 | 108 | 176 | 25 |
| Gestión de proyecto | 5 de 5 | 158 | 136 | 184 | 21 |
| Liderazgo técnico | 5 de 5 | 150 | 136 | 180 | 18 |
| DevOps | 5 de 5 | 96 | 80 | 104 | 10 |

## Cada llamada

| Llamada | Horas base | Precio (USD) | Semanas (propuestas) | Tareas | Puntos por confirmar | Etapas alargadas por Python |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,880 | 278,681 | 16 (16) | 21 | 3 | 0 |
| 2 | 2,200 | 315,561 | 17 (17) | 21 | 2 | 0 |
| 3 | 1,640 | 260,289 | 16 (16) | 20 | 3 | 0 |
| 4 | 1,828 | 277,867 | 17 (17) | 22 | 2 | 0 |
| 5 | 1,848 | 280,424 | 16 (16) | 20 | 3 | 0 |

## Puntos de alcance por confirmar

En el recorrido directo los redacta el modelo, así que el mismo punto puede salir con palabras distintas: hay que leerlos para ver si coinciden. Con el inventario, son los requisitos opcionales o condicionados, con la descripción que les dio el modelo.

**Llamada 1**
- Quién produce los contenidos de la formación Parte 46 (módulos, videos y cuestionarios) y quién los traduce al español: no quedó decidido, así que no están estimados.
- Formación de riesgos del lugar para contratistas: el cliente quiere incluirla si es posible, pero no es lo principal. No está estimada.
- Consulta del asistente sin conexión: el modelo de lenguaje necesita conexión. No quedó decidido si basta con sincronizar cuando vuelva la cobertura o si quieren consultar los manuales sin conexión. No está estimada.

**Llamada 2**
- Formación de riesgos del lugar para los contratistas que entran a las canteras: el cliente dijo que sería mejor incluirla, pero no lo decidió. No está estimada.
- Quién produce los videos y los cuestionarios de los módulos de la Parte 46, y quién traduce el contenido al español: no se decidió en la reunión. No están estimados.

**Llamada 3**
- Formación de riesgos del lugar para los contratistas que entran a las canteras: la mencionó el gerente de EHS como deseable, pero no se decidió. No está estimada.
- Despliegue en las demás canteras y en las plantas de trituración tras el piloto: el cliente habló de empezar con dos canteras, pero no decidió el alcance del resto. No está estimado.
- Quién produce los videos de formación y quién traduce al español los módulos y los manuales: no se decidió. No están estimados.

**Llamada 4**
- Quién produce los videos y el contenido de los módulos de la Parte 46 en inglés y español: la consultora o el cliente. No está estimado.
- Formación de riesgos del lugar para los contratistas que entran a las canteras: el cliente la pidió como opcional. No está estimada.

**Llamada 5**
- Formación de riesgos del lugar para contratistas que entran a las canteras: el cliente lo mencionó como deseable, sin decidirlo. No está estimada.
- Quién produce los videos y la traducción de los módulos de la Parte 46 al español: no se decidió. No están estimados.
- Alcance del despliegue después del piloto: se estima el resto de las nueve canteras, pero las tres plantas de trituración y lavado no se mencionaron.
