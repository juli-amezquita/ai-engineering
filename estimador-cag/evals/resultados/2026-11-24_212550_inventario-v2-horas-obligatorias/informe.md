# Consistencia del inventario: inventario-v2-horas-obligatorias

- Transcripción: `transcripciones/onboarding_seguridad_canteras.txt` (huella 402c1ff99f4f)
- Modelo: claude-haiku-5-5 · prompt 927c8c24c2b3 · commit 96aef76 con cambios sin commit en app/
- Fecha: 2026-11-24T21:25:50
- Llamadas válidas: 10 de 10 · costo total 0.0438 USD

## Cifras

Las horas son base, sin el 10 % de imprevistos. Las del catálogo las calcula Python; las que quedan a revisar las pone el modelo.

| | Media | Mediana | Mínimo | Máximo | Amplitud | CV |
|---|---:|---:|---:|---:|---:|---:|
| Horas base | 1,879 | 1,871 | 1,775 | 1,987 | 12 % | 4 % |
| Horas del catálogo | 895 | 888 | 848 | 1,024 | 21 % | 6 % |
| Horas a revisar (del modelo) | 178 | 182 | 107 | 250 | 134 % | 28 % |
| Requisitos acordados | 11 | 11 | 10 | 12 | 20 % | 8 % |
| Requisitos no acordados | 2 | 2 | 1 | 3 | 200 % | 29 % |

**Plataforma:** web en 10 de 10.

**Horas que faltaban:** 2 de 10 inventarios necesitaron una segunda llamada para completar horas; quedan 0 partidas sin horas.

## Componentes acordados

| Componente | Llamadas en las que aparece | Tamaños | Unidades por llamada |
|---|---:|---|---:|
| Cuentas de usuario y roles | 10 de 10 | M ×5, S ×5 | 1-1 |
| Carga de archivos y multimedia | 2 de 10 | M ×1, S ×1 | 0-1 |
| Notificaciones y recordatorios | 10 de 10 | S ×10 | 1-1 |
| Varios idiomas | 10 de 10 | S ×10 | 1-1 |
| Modo sin conexión y sincronización | 10 de 10 | M ×9, S ×1 | 1-1 |
| Lecciones, cuestionarios y progreso | 10 de 10 | M ×10 | 1-1 |
| Integración con un sistema de RR. HH. o nómina | 3 de 10 | S ×3 | 0-1 |
| Paneles y reportes | 10 de 10 | M ×10 | 1-1 |
| Analítica de personas con historial | 10 de 10 | M ×10 | 1-1 |
| Encuestas a empleados | 10 de 10 | S ×10 | 1-1 |
| Asistente con IA sobre documentos propios (RAG) | 10 de 10 | M ×10 | 1-1 |
| Documentos generados y firmas en pantalla | 10 de 10 | M ×6, S ×5 | 1-2 |
| Formación de usuarios y gestión del cambio | 1 de 10 | M ×1 | 0-1 |
| A medida | 2 de 10 | M ×1, S ×1 | 0-1 |

## Cada llamada

| Llamada | Plataforma | Horas base | Catálogo | A revisar | Acordados | Opcionales | Condicionados | Excluidos | Decisiones abiertas |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | web | 1,971 | 928 | 212 | 11 | 1 | 1 | 0 | 2 |
| 2 | web | 1,976 | 912 | 232 | 12 | 1 | 1 | 0 | 2 |
| 3 | web | 1,775 | 888 | 107 | 11 | 1 | 2 | 0 | 3 |
| 4 | web | 1,793 | 848 | 160 | 10 | 1 | 2 | 0 | 3 |
| 5 | web | 1,890 | 876 | 204 | 12 | 1 | 2 | 0 | 2 |
| 6 | web | 1,852 | 848 | 204 | 10 | 1 | 2 | 0 | 3 |
| 7 | web | 1,914 | 848 | 250 | 10 | 1 | 1 | 0 | 2 |
| 8 | web | 1,840 | 888 | 155 | 11 | 1 | 1 | 0 | 2 |
| 9 | web | 1,987 | 1,024 | 128 | 12 | 1 | 1 | 0 | 2 |
| 10 | web | 1,796 | 888 | 123 | 10 | 1 | 0 | 0 | 4 |

## Lo que no se acordó y las decisiones abiertas

**Llamada 1**
- condicionado: Piloto de la aplicación en dos canteras, con formación de usuarios y preparación del despliegue
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras, si se puede incluir
- Decisión abierta: Si la integración con el HRIS solo lee empleados o también escribe (se asume: solo lectura de empleados)
- Decisión abierta: Quién produce los videos y cuestionarios de los módulos de la Parte 46 (se asume: el cliente)

**Llamada 2**
- condicionado: Piloto de incorporación en dos canteras, con formación a usuarios y acompañamiento en sus sedes
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: Qué sistema HRIS se integra y si la integración solo lee empleados o también escribe (se asume: Solo lectura de empleados)
- Decisión abierta: Si el despliegue empieza con un piloto en dos canteras o cubre todas las canteras desde el inicio (se asume: Piloto en dos canteras)

**Llamada 3**
- condicionado: Piloto en dos canteras con formación de usuarios y gestión del cambio
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- condicionado: Integración con el HRIS que tiene API para datos de empleados
- Decisión abierta: ¿El asistente de documentos funciona sin conexión en la tablet? (se asume: Con conexión)
- Decisión abierta: ¿Empezar con un piloto en dos canteras o desplegar en todas? (se asume: Piloto en dos canteras)
- Decisión abierta: ¿Qué datos se intercambian con el HRIS? (se asume: Solo lectura de empleados)

**Llamada 4**
- condicionado: Leer empleados del HRIS por API para dar de alta a las personas nuevas y cruzar la rotacion
- opcional: Formacion de riesgos del lugar para contratistas que entran a las canteras
- condicionado: Acompanar el piloto en dos canteras y preparar el despliegue al resto
- Decisión abierta: ¿Los datos de empleados llegan del HRIS por API o se cargan a mano? (se asume: Carga manual de empleados)
- Decisión abierta: ¿Se incluye en la primera version la formacion de riesgos del lugar para contratistas? (se asume: No, en una fase posterior)
- Decisión abierta: ¿Se despliega primero en dos canteras o en las nueve a la vez? (se asume: Piloto en dos canteras)

**Llamada 5**
- condicionado: Lectura de empleados desde el HRIS para la incorporación y la rotación
- condicionado: Piloto en dos canteras con formación a usuarios y gestión del cambio
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: De dónde salen los datos de empleados para la incorporación y la rotación (se asume: API del HRIS)
- Decisión abierta: Cómo se muestran los resultados de la encuesta por supervisor sin identificar a las personas (se asume: Solo resultados agregados por cantera)

**Llamada 6**
- condicionado: Lectura de datos de empleados desde el HRIS de la empresa, que tiene API, para cruzar con la rotación
- condicionado: Piloto en dos canteras antes de desplegar en todas, con formación y acompañamiento de los usuarios
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: Qué sistema de RR. HH. o nómina se usa como fuente de datos de empleados (se asume: Integración con el HRIS actual por API)
- Decisión abierta: Si la formación de riesgos del lugar para contratistas entra en el alcance (se asume: Dejarla fuera de esta entrega)
- Decisión abierta: Si se empieza con un piloto en dos canteras o se despliega en todas a la vez (se asume: Piloto en dos canteras)

**Llamada 7**
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- condicionado: Piloto en dos canteras con formación a usuarios y preparación del despliegue
- Decisión abierta: ¿Cómo entran los datos de las personas nuevas a la aplicación? (se asume: Alta manual por el supervisor o RR. HH.)
- Decisión abierta: ¿Se incluye en esta fase la formación de riesgos para contratistas? (se asume: Dejarla para una fase posterior)

**Llamada 8**
- condicionado: Lectura de datos de empleados del sistema de RR. HH. existente, que tiene API, para la incorporación y el cruce de rotación.
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras.
- Decisión abierta: ¿De dónde salen los datos de empleados para el cruce de rotación y la incorporación: integración directa con el HRIS por API o exportaciones periódicas? (se asume: Integración directa con el HRIS por API)
- Decisión abierta: ¿La formación de riesgos del lugar para contratistas entra en esta fase? (se asume: No, en una fase posterior)

**Llamada 9**
- condicionado: Piloto de la app en dos canteras antes del despliegue completo
- opcional: Formación de riesgos del lugar para contratistas que entran a las canteras
- Decisión abierta: Si el HRIS solo se lee o también se escribe (se asume: solo lectura)
- Decisión abierta: Si el piloto empieza en dos canteras o en todas (se asume: piloto en dos canteras)

**Llamada 10**
- opcional: Formación en riesgos del lugar para contratistas que entran a las canteras (opcional, no es lo principal)
- Decisión abierta: Fuente de datos de altas y bajas para la analítica de rotación (se asume: Integración con el HRIS)
- Decisión abierta: Tecnología de la app para tablet: web instalable o app nativa (se asume: Web instalable)
- Decisión abierta: Alcance del primer despliegue (se asume: Piloto en dos canteras)
- Decisión abierta: Formación de contratistas en esta fase (se asume: Incluir como opcional fuera del precio base)

## Horas que puso el modelo

Son las que hay que revisar: el catálogo no tiene referencia.

**Llamada 1:** 212 h
- Documentos generados y firmas en pantalla (S): Registro de la formación por tarea firmado en la tablet y generación automática del certificado 5000-23, guardado en la aplicación: 84 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días de cada persona nueva: 40 h
- Analítica de personas con historial (M): Cruce de los resultados de seguimiento con la rotación por cantera y por supervisor, con historial de altas, bajas y cambios: 88 h

**Llamada 2:** 232 h
- A medida (M): Registro en la tablet, por parte del supervisor, de la formación de cada tarea de la persona nueva, con firma en la misma pantalla: 80 h
- Documentos generados y firmas en pantalla (S): Generación automática del certificado 5000-23 y guardado de cada certificado firmado: 32 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días de la persona nueva, con resultados agregados: 40 h
- Analítica de personas con historial (M): Cruce de los resultados del seguimiento con la rotación por cantera y por supervisor: 80 h

**Llamada 3:** 107 h
- A medida (S): Registro de la formación de cada tarea que el supervisor marca en la tablet y firma en el momento: 19 h
- Documentos generados y firmas en pantalla (S): Generación automática del certificado 5000-23 en PDF, firmado en pantalla y guardado: 26 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días de cada persona nueva: 20 h
- Analítica de personas con historial (M): Cruce de los resultados de seguimiento con la rotación por cantera y por supervisor: 42 h

**Llamada 4:** 160 h
- Documentos generados y firmas en pantalla (M): Generar el certificado 5000-23 de forma automatica, guardarlo y firmarlo en la tablet: 54 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 dias de la incorporacion: 36 h
- Analítica de personas con historial (M): Cruce de la rotacion y de los resultados de seguimiento por cantera y por supervisor: 70 h

**Llamada 5:** 204 h
- Documentos generados y firmas en pantalla (S): Registro de la formación de cada tarea marcado por el supervisor en la tablet y firmado en pantalla: 54 h
- Documentos generados y firmas en pantalla (S): Generación automática del certificado 5000-23 en PDF y guardado de cada certificado: 42 h
- Encuestas a empleados (S): Encuesta corta a los 30, 60 y 90 días de la incorporación con envío programado y resultados agregados: 42 h
- Analítica de personas con historial (M): Historial de personas y rotación a 90 días por cantera y por supervisor, cruzado con la encuesta: 66 h

**Llamada 6:** 204 h
- Documentos generados y firmas en pantalla (M): Firma en la tablet por parte del supervisor y generación automática y guardado del certificado 5000-23: 66 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días de cada persona nueva: 48 h
- Analítica de personas con historial (M): Cruce del seguimiento de la persona nueva con la rotación por cantera y por supervisor, con historial de altas, bajas y cambios de jefe: 90 h
- Completada en una segunda llamada: Firma en la tablet por parte del supervisor y generación automática y guardado del certificado 5000-23
- Completada en una segunda llamada: Cruce del seguimiento de la persona nueva con la rotación por cantera y por supervisor, con historial de altas, bajas y cambios de jefe

**Llamada 7:** 250 h
- Documentos generados y firmas en pantalla (M): El supervisor marca en la tablet la formación de cada tarea y firma ahí mismo, y el certificado 5000-23 se genera y se guarda solo: 76 h
- Encuestas a empleados (S): Encuesta corta a 30, 60 y 90 días de la incorporación, con resultados agregados: 92 h
- Analítica de personas con historial (M): Cruce de la encuesta con la rotación por cantera y por supervisor, a partir del historial de altas y bajas: 82 h
- Completada en una segunda llamada: Encuesta corta a 30, 60 y 90 días de la incorporación, con resultados agregados

**Llamada 8:** 155 h
- Documentos generados y firmas en pantalla (M): Certificado 5000-23 generado automáticamente al completar la formación, firmado en la tablet por el supervisor y guardado.: 30 h
- Encuestas a empleados (S): Encuesta corta a los 30, 60 y 90 días de cada nueva persona, con resultados agregados.: 27 h
- Analítica de personas con historial (M): Cruce de la rotación de los nuevos por cantera y por supervisor, con historial de cada persona (altas, bajas y cambios de jefe).: 62 h
- Formación de usuarios y gestión del cambio (M): Piloto de la aplicación en dos canteras, con formación de usuarios y preparación del despliegue antes de la temporada de contratación.: 36 h

**Llamada 9:** 128 h
- Documentos generados y firmas en pantalla (M): Marcar en la tablet la formación de cada tarea, firma del supervisor y generación automática y guardado del certificado 5000-23: 48 h
- Encuestas a empleados (S): Encuesta corta de seguimiento a los 30, 60 y 90 días, con resultados agregados: 20 h
- Analítica de personas con historial (M): Cruce de la encuesta con la rotación por cantera y por supervisor, con historial de altas y bajas: 60 h

**Llamada 10:** 123 h
- Documentos generados y firmas en pantalla (M): El supervisor marca en la tablet la formación de cada tarea, firma ahí mismo y el certificado 5000-23 se genera solo y queda guardado: 32 h
- Encuestas a empleados (S): Encuesta corta a los 30, 60 y 90 días de la incorporación: 29 h
- Analítica de personas con historial (M): Cruce de la rotación y de los resultados de la encuesta por cantera y por supervisor, para saber si la incorporación funciona: 62 h
