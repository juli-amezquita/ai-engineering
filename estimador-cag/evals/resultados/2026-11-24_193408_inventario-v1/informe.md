# Consistencia del inventario: inventario-v1

- Transcripción: `transcripciones/onboarding_seguridad_canteras.txt` (huella 402c1ff99f4f)
- Modelo: claude-haiku-5-5 · prompt a0848d83f1e7 · commit 96aef76 con cambios sin commit en app/
- Fecha: 2026-11-24T19:34:08
- Llamadas válidas: 10 de 10 · costo total 0.0430 USD

## Cifras

Las horas son base, sin el 10 % de imprevistos. Las del catálogo las calcula Python; las que quedan a revisar las pone el modelo.

| | Media | Mediana | Mínimo | Máximo | Amplitud | CV |
|---|---:|---:|---:|---:|---:|---:|
| Horas base | 1,885 | 1,882 | 1,713 | 2,033 | 19 % | 5 % |
| Horas del catálogo | 906 | 888 | 848 | 968 | 14 % | 5 % |
| Horas a revisar (del modelo) | 171 | 168 | 101 | 298 | 195 % | 34 % |
| Requisitos acordados | 11 | 10 | 10 | 12 | 20 % | 7 % |
| Requisitos no acordados | 2 | 2 | 1 | 3 | 200 % | 36 % |

**Plataforma:** web en 10 de 10.

**Horas que faltaban:** 0 de 10 inventarios necesitaron una segunda llamada para completar horas; quedan 2 partidas sin horas.

## Componentes acordados

| Componente | Llamadas en las que aparece | Tamaños | Unidades por llamada |
|---|---:|---|---:|
| Cuentas de usuario y roles | 9 de 10 | M ×6, S ×3 | 0-1 |
| Carga de archivos y multimedia | 1 de 10 | M ×1 | 0-1 |
| Notificaciones y recordatorios | 10 de 10 | S ×10 | 1-1 |
| Varios idiomas | 10 de 10 | S ×10 | 1-1 |
| Modo sin conexión y sincronización | 10 de 10 | M ×10 | 1-1 |
| Lecciones, cuestionarios y progreso | 10 de 10 | M ×10 | 1-1 |
| Integración con un sistema de RR. HH. o nómina | 4 de 10 | S ×4 | 0-1 |
| Paneles y reportes | 10 de 10 | M ×10 | 1-1 |
| Analítica de personas con historial | 10 de 10 | M ×10 | 1-1 |
| Encuestas a empleados | 10 de 10 | M ×1, S ×9 | 1-1 |
| Asistente con IA sobre documentos propios (RAG) | 10 de 10 | M ×10 | 1-1 |
| Documentos generados y firmas en pantalla | 10 de 10 | M ×8, S ×3 | 1-2 |
| A medida | 1 de 10 | M ×1 | 0-1 |

## Cada llamada

| Llamada | Plataforma | Horas base | Catálogo | A revisar | Acordados | Opcionales | Condicionados | Excluidos | Decisiones abiertas |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | web | 1,776 | 888 | 108 | 10 | 1 | 1 | 0 | 2 |
| 2 | web | 1,877 | 928 | 143 | 11 | 1 | 1 | 0 | 2 |
| 3 | web | 1,849 | 888 | 162 | 10 | 1 | 0 | 0 | 1 |
| 4 | web | 1,957 | 944 | 186 | 11 | 1 | 2 | 0 | 1 |
| 5 | web | 1,917 | 968 | 132 | 11 | 0 | 1 | 0 | 2 |
| 6 | web | 2,033 | 888 | 298 | 11 | 1 | 1 | 0 | 2 |
| 7 | web | 1,887 | 888 | 190 | 10 | 1 | 2 | 0 | 2 |
| 8 | web | 1,812 | 848 | 174 | 10 | 1 | 2 | 0 | 3 |
| 9 | web | 2,025 | 968 | 212 | 12 | 1 | 1 | 0 | 2 |
| 10 | web | 1,713 | 848 | 101 | 10 | 1 | 2 | 0 | 1 |

## Lo que no se acordó y las decisiones abiertas

**Llamada 1**
- condicionado: Piloto de la app en dos canteras, con acompanamiento de los supervisores en sus sedes
- opcional: Formacion de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: ¿Se integra la app con el HRIS de la empresa para leer datos de empleados? (se asume: No, la app gestiona sus propios datos)
- Decisión abierta: ¿Se incluye la formacion de riesgos del lugar para contratistas en la primera version? (se asume: No, en una fase posterior)

**Llamada 2**
- condicionado: Piloto en dos canteras y preparación del despliegue
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: Qué tipo de integración tendrá el HRIS de la empresa (se asume: Solo lectura con API estándar)
- Decisión abierta: Si el asistente funciona sin conexión en la tablet (se asume: Solo con conexión)

**Llamada 3**
- opcional: Formación de riesgos del lugar para los contratistas que entran a las canteras.
- Decisión abierta: Cómo se carga la plantilla en la aplicación: por API del HRIS o por carga manual (se asume: Carga manual de la plantilla)

**Llamada 4**
- condicionado: Lectura de empleados, cantera y supervisor desde el HRIS por API para la analítica de rotación
- condicionado: Piloto en dos canteras: formar a usuarios y acompañar el arranque
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: Origen de las altas y bajas para la analítica de rotación (se asume: Integración con el HRIS por API)

**Llamada 5**
- condicionado: Piloto de la app en dos canteras antes del despliegue en todas, con formación de usuarios y acompañamiento en sus sedes
- Decisión abierta: ¿Qué HRIS usan exactamente y qué datos se leen o escriben desde la app? (se asume: Solo lectura de empleados y supervisores)
- Decisión abierta: ¿Se incluye en esta fase la formación de riesgos del lugar para contratistas que entran a las canteras? (se asume: Dejar para una fase posterior)

**Llamada 6**
- condicionado: Piloto de la app en dos canteras antes de desplegar en todas
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: ¿Qué HRIS usa el cliente y necesita la integración solo lectura o también escritura? (se asume: Solo lectura de empleados, cantera y supervisor)
- Decisión abierta: ¿Se despliega primero como piloto en dos canteras o en todas las canteras? (se asume: Piloto en dos canteras)

**Llamada 7**
- condicionado: Lectura de empleados desde el HRIS, que tiene API, para alimentar la incorporación y la rotación
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- condicionado: Piloto en dos canteras con formación a usuarios y acompañamiento en sus sedes antes del despliegue
- Decisión abierta: Cómo se conecta la app con el HRIS para leer los datos de empleados (se asume: Integrar con la API del HRIS)
- Decisión abierta: Si se empieza con un piloto en dos canteras o se despliega en todas a la vez (se asume: Piloto en dos canteras antes de desplegar)

**Llamada 8**
- condicionado: Lectura de altas y bajas de empleados desde el HRIS de la empresa para el análisis de rotación
- condicionado: Piloto en dos canteras antes del despliegue completo
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: ¿Qué sistema HRIS usan y qué datos de altas y bajas se pueden leer por API? (se asume: Lectura de altas y bajas por API)
- Decisión abierta: ¿Se incluye la formación de riesgos del lugar para contratistas en este alcance? (se asume: No, en una fase posterior)
- Decisión abierta: ¿El proyecto empieza con un piloto en dos canteras o con el despliegue en las nueve canteras? (se asume: Piloto en dos canteras)

**Llamada 9**
- condicionado: Piloto de la solución en dos canteras, con formación a los usuarios y acompañamiento en sus sedes
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: ¿Qué sistema de RR. HH. es el HRIS actual? (se asume: Otro)
- Decisión abierta: ¿La formación de contratistas entra en esta fase? (se asume: Fase posterior)

**Llamada 10**
- condicionado: Lectura de datos de personas, cantera y supervisor desde el HRIS de la empresa
- condicionado: Piloto en dos canteras con formación a usuarios y acompañamiento en sus sedes
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: ¿Se conecta la app al HRIS para tomar los datos de las personas, su cantera y su supervisor? (se asume: Integrar con el HRIS)

## Horas que puso el modelo

Son las que hay que revisar: el catálogo no tiene referencia.

**Llamada 1:** 108 h
- Documentos generados y firmas en pantalla (M): El supervisor marca en la tablet la formacion de cada tarea y firma ahi mismo; el certificado 5000-23 se genera solo y queda guardado: 36 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 dias de cada persona nueva: 16 h
- Analítica de personas con historial (M): Analisis de la rotacion en los primeros 90 dias por cantera y por supervisor, para saber si la incorporacion funciona: 56 h

**Llamada 2:** 143 h
- Documentos generados y firmas en pantalla (M): El supervisor marca en la tablet la formación de cada tarea, firma ahí mismo, y el certificado 5000-23 se genera solo y queda guardado: 45 h
- Encuestas a empleados (S): Encuesta corta a los 30, 60 y 90 días sobre la incorporación, con resultados agregados: 34 h
- Analítica de personas con historial (M): Cruce de la rotación en los primeros 90 días por cantera y por supervisor: 64 h

**Llamada 3:** 162 h
- Documentos generados y firmas en pantalla (M): El supervisor marca en la tablet la formación de cada tarea y firma ahí mismo; el certificado 5000-23 se genera automáticamente y queda guardado.: 56 h
- Encuestas a empleados (S): Encuesta corta a los 30, 60 y 90 días desde la contratación, con resultados agregados.: 44 h
- Analítica de personas con historial (M): Cruce del seguimiento de incorporación con la rotación por cantera y por supervisor, con historial de altas y bajas.: 62 h

**Llamada 4:** 186 h
- Documentos generados y firmas en pantalla (M): El supervisor marca en la tablet la formación de cada tarea y firma ahí mismo; el certificado 5000-23 se genera solo y queda guardado: 56 h
- Encuestas a empleados (S): Encuesta corta a los 30, 60 y 90 días desde la contratación, con resultados agregados: 30 h
- Analítica de personas con historial (M): Cruce de la rotación en los primeros 90 días por cantera y por supervisor, con historia de altas y bajas: 100 h

**Llamada 5:** 132 h
- Documentos generados y firmas en pantalla (M): Registro en tablet por parte del supervisor de la formación de cada tarea, con firma en pantalla y certificado 5000-23 generado y guardado automáticamente: 40 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días de cada persona nueva, con resultados agregados: 20 h
- Analítica de personas con historial (M): Cruce de la encuesta y de la rotación con la historia de cada persona, por cantera y por supervisor: 72 h

**Llamada 6:** 298 h
- Documentos generados y firmas en pantalla (M): Registro en la tablet por el supervisor de la formación de cada tarea y firma en pantalla de la persona y del supervisor: 80 h
- Documentos generados y firmas en pantalla (S): Generación automática del certificado MSHA 5000-23 al completar la formación, con almacenamiento de cada certificado: 26 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días de cada incorporación, con resultados agregados: 0 h
- Analítica de personas con historial (M): Cruce de los resultados de seguimiento con la rotación por cantera y por supervisor, con historial de altas, bajas y cambios de supervisor: 192 h

**Llamada 7:** 190 h
- Documentos generados y firmas en pantalla (M): Registro de formación por tarea firmado en la tablet por el supervisor, con certificado 5000-23 generado automáticamente y guardado: 54 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días de cada persona nueva: 28 h
- Analítica de personas con historial (M): Cruce de la encuesta y del historial de personas con la rotación por cantera y por supervisor: 108 h

**Llamada 8:** 174 h
- Documentos generados y firmas en pantalla (M): Firma en pantalla del supervisor y generación automática y guardado del certificado 5000-23 de MSHA: 0 h
- Encuestas a empleados (M): Encuesta corta a los 30, 60 y 90 días de cada persona contratada, con resultados agregados: 64 h
- Analítica de personas con historial (M): Análisis de rotación por cantera y por supervisor a partir del historial de altas y bajas: 110 h

**Llamada 9:** 212 h
- A medida (M): Registro de formación por tarea que el supervisor marca en la tablet antes de que el trabajador haga cada tarea: 54 h
- Documentos generados y firmas en pantalla (S): Certificado 5000-23 generado automáticamente, guardado y firmado en pantalla por el supervisor: 48 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días de la incorporación: 38 h
- Analítica de personas con historial (M): Análisis de rotación de los nuevos por cantera y por supervisor, a partir de la historia de cada persona: 72 h

**Llamada 10:** 101 h
- Documentos generados y firmas en pantalla (S): Firma en pantalla del supervisor sobre la formación de cada tarea y generación automática y guardado del certificado 5000-23: 26 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días de cada persona nueva: 27 h
- Analítica de personas con historial (M): Cruce de los resultados del seguimiento con la rotación por cantera y por supervisor: 48 h
