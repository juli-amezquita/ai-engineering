# Ejemplos de salida

Salida real del estimador con la transcripción de prueba [`onboarding_seguridad_canteras.txt`](../transcripciones/onboarding_seguridad_canteras.txt), sin `scope_changes`. Se generó el 2026-11-22 con `claude-haiku-5-5` y el mismo código de esta rama. Sirve para ver qué devuelve el servicio sin tener una API key.

| Archivo | Qué es |
|---|---|
| [`respuesta.json`](respuesta.json) | La respuesta completa de `POST /api/v1/estimate` |
| [`informe_interno.md`](informe_interno.md) | El campo `estimation`: el informe interno de la consultora, con costos y márgenes |
| [`propuesta_cliente.md`](propuesta_cliente.md) | El campo `client_proposal`: la propuesta de valor y de negocio para el cliente |

**La llamada:** 53 segundos, 12,830 tokens de salida con el thinking incluido y unos 0.0093 USD.

**El resultado:** 17 semanas en 4 etapas, 1,544 horas base y 231,801 USD, con un margen neto del 30.0 %. La reunión dejó estos puntos de alcance sin decidir, así que no están estimados y la propuesta los muestra como "Puntos por confirmar":

- Formación de riesgos del lugar para contratistas que entran a las canteras: el cliente la mencionó como deseable, pero no es lo principal y no se decidió. No está estimada.
- Quién produce los videos, los cuestionarios y el contenido de los módulos de la Parte 46: la reunión no lo decidió. No está estimado.
- Traducción de los manuales de seguridad al español si están solo en inglés: no se decidió. No está estimada.

La misma transcripción puede dar estimaciones distintas en cada llamada: ver "Limitaciones conocidas" en el [README del proyecto](../README.md).
