# Informe interno: App de incorporación y formación MSHA Parte 46 para canteras

> [!warning] Confidencial
> Solo para la consultora: incluye costos, márgenes y tarifas internas. Al cliente se le envía la propuesta.

- **Tipo de proyecto:** App para tablet sin conexión con panel web y asistente de IA
- **Cliente:** Productor de áridos del Valle Central de California, con unas 350 personas en nueve canteras y tres plantas de trituración y lavado, que contrata unas 120 personas al año, sobre todo entre marzo y junio.

## 1. Resumen

| Concepto | Valor |
|---|---|
| Duración | 17 semanas (4 etapas) |
| Horas base / imprevistos / totales | 1,544 / 154.4 / 1,698.4 |
| Equipo | 13 profesionales, 2.5 personas a tiempo completo de media |
| Precio total | 231,801 USD |
| Honorarios / gastos reembolsables | 228,126 USD / 3,675 USD |
| Tarifa media (honorarios ÷ horas totales) | 134.32 USD/h |
| Costo del equipo | 116,683 USD |
| Utilidad neta / margen neto | 69,535 USD / 30.0 % |
| Recargo de rentabilidad sobre el costo | 45.3 % |
| Caja máxima que hay que adelantar | 45,196 USD |

**Alertas:**
- ⚠️ La tarifa media queda un 10.5 % por debajo del mercado. Cobrando 150 USD/h, la utilidad neta subiría a 93,671 USD (margen del 36.2 %): fijar el precio por el margen objetivo deja ese dinero en la mesa.
- ⚠️ La reunión dejó 3 puntos de alcance sin decidir, que no están estimados (sección 2). Decide qué entra y vuelve a estimar indicando los cambios de alcance.
- ⚠️ Tarifas fuera del rango de 75-175 USD/h de las consultoras pequeñas (Cleveroad): Liderazgo técnico 233.60, IA / ML 197.97, Diseño UX/UI 28.66, Frontend 35.83, Full-stack 37.62, Móvil 39.41, QA 30.46. Las más bajas pueden dejar ver que ese perfil trabaja desde un país de menor costo; las más altas invitan a negociar.
- ⚠️ Un margen neto del 30 % es alto: más del doble de la media de las agencias pequeñas (12 %), aunque dentro del 25-40 % de las especializadas (Promethean, vía Haus Advisors). Es alcanzable sobre todo porque los contratistas solo cobran las horas trabajadas.

## 2. Alcance

App para tablet, en inglés y español y sin conexión, que guía la formación MSHA Parte 46 de cada persona nueva, registra la formación de cada tarea con la firma del supervisor y genera y archiva el formulario 5000-23. Incluye un panel de EHS por cantera, avisos de reciclaje anual, un asistente de IA que responde solo con los unos 40 manuales citando la fuente y deriva al supervisor cuando no hay respuesta, y un seguimiento a 30, 60 y 90 días cruzado con la rotación por cantera y supervisor. Se prueba en un piloto de dos canteras antes de la temporada de contratación y termina con el despliegue y dos semanas de hipercuidado. El contenido de los módulos y los videos no está incluido en la estimación.

**Puntos que la reunión dejó sin decidir.** No están estimados ni incluidos en la propuesta: decídelos y vuelve a estimar indicando los cambios de alcance.

- Formación de riesgos del lugar para contratistas que entran a las canteras: el cliente la mencionó como deseable, pero no es lo principal y no se decidió. No está estimada.
- Quién produce los videos, los cuestionarios y el contenido de los módulos de la Parte 46: la reunión no lo decidió. No está estimado.
- Traducción de los manuales de seguridad al español si están solo en inglés: no se decidió. No está estimada.

## 3. Cronograma por etapa

| Etapa | Semanas | Duración | Propuesta del modelo | Cronograma |
|---|---|---|---|---|
| 1. Descubrimiento y diseño | 1-3 | 3 semanas | igual | `███··············` |
| 2. Construcción | 4-11 | 8 semanas | igual | `···████████······` |
| 3. Piloto en dos canteras | 12-15 | 4 semanas | igual | `···········████··` |
| 4. Despliegue e hipercuidado | 16-17 | 2 semanas | igual | `···············██` |

## 4. Desglose de tareas

Horas base, sin imprevistos. Las horas de cada tarea se reparten por igual entre las semanas de sus etapas.

| Tarea | Etapas | Semanas | Horas por perfil | Horas | Cronograma |
|---|---|---|---|---|---|
| Descubrimiento con visitas a dos canteras, mapa del proceso de incorporación y revisión de la Parte 46 con EHS | 1 | 1-3 | Gestión de proyecto 24, Consultoría de RR. HH. 24, Diseño UX/UI 16, Liderazgo técnico 16 | 80 | `███··············` |
| Diseño UX/UI de la tablet sin conexión, en inglés y español, con pruebas con supervisores y personas nuevas | 1-2 | 1-11 | Diseño UX/UI 96 | 96 | `███████████······` |
| Arquitectura, modelo de datos y sincronización sin conexión | 1-2 | 1-11 | Liderazgo técnico 48, Backend 56 | 104 | `███████████······` |
| Integración con el HRIS por API para los datos de la persona nueva | 2 | 4-11 | Backend 48 | 48 | `···████████······` |
| Módulos de la Parte 46 con videos cortos, cuestionarios y seguimiento del progreso | 2 | 4-11 | Móvil 80 | 80 | `···████████······` |
| Marcado de la formación por tarea y firma del supervisor en la tablet | 2 | 4-11 | Móvil 120 | 120 | `···████████······` |
| Generación y archivo automático del certificado 5000-23 | 2 | 4-11 | Backend 40 | 40 | `···████████······` |
| Avisos de reciclaje anual y de formación próxima a vencer | 2 | 4-11 | Backend 16 | 16 | `···████████······` |
| Panel de EHS por cantera: al día, pendiente y que vence este mes | 2 | 4-11 | Frontend 64, Full-stack 40 | 104 | `···████████······` |
| Ingesta y preparación de los unos 40 manuales de seguridad y procedimientos | 1-2 | 1-11 | Ingeniería de datos 48 | 48 | `███████████······` |
| Asistente de respuestas con cita de la fuente y derivación al supervisor | 2 | 4-11 | IA / ML 120, Backend 24 | 144 | `···████████······` |
| Seguimiento a 30, 60 y 90 días y cruce con la rotación por cantera y supervisor | 2 | 4-11 | Ciencia de datos 40, Consultoría de RR. HH. 16, Frontend 24 | 80 | `···████████······` |
| Infraestructura, entornos de prueba sin conexión, CI/CD y monitorización | 1-2 | 1-11 | DevOps 80 | 80 | `███████████······` |
| Pruebas en tablets reales dentro de canteras sin cobertura | 2-3 | 4-15 | QA 120 | 120 | `···████████████··` |
| Piloto en dos canteras: soporte, revisión de respuestas del asistente y ajustes | 3 | 12-15 | Gestión de proyecto 24, Consultoría de RR. HH. 24, Móvil 32, IA / ML 24, QA 16, Liderazgo técnico 16 | 136 | `···········████··` |
| Despliegue en nueve canteras y tres plantas, formación a supervisores y RR. HH., e hipercuidado | 4 | 16-17 | Gestión de proyecto 24, Consultoría de RR. HH. 16, Backend 24, Móvil 16, IA / ML 8 | 88 | `···············██` |
| Liderazgo técnico: revisiones de código, decisiones de arquitectura y seguridad de los datos | 1-4 | 1-17 | Liderazgo técnico 64 | 64 | `█████████████████` |
| Gestión del proyecto: planificación, seguimiento semanal, comité mensual y riesgos | 1-4 | 1-17 | Gestión de proyecto 96 | 96 | `█████████████████` |
| **Total, sin imprevistos** | | | | **1,544** | |

## 5. Costo por hora de cada perfil

| Perfil | Ubicación | Modalidad | Base del costo | Costo por hora |
|---|---|---|---|---|
| Gestión de proyecto | Los Ángeles | Plantilla W-2 | BLS LA, mediana 52.07 USD/h × 1.43 × 1,880 h ÷ 1,381 h facturables | 101.25 |
| Consultoría de RR. HH. | Los Ángeles | Plantilla W-2 | BLS LA, mediana 46.78 USD/h × 1.43 × 1,880 h ÷ 1,381 h facturables | 90.97 |
| Liderazgo técnico | Los Ángeles | Plantilla W-2 | BLS LA, mediana 77.37 USD/h × 1.43 × 1,880 h ÷ 1,381 h facturables | 150.45 |
| Backend | EE. UU. | Contratista por hora | KORE1, punto medio del pago al contratista: 65.00 USD/h | 65.00 |
| Ingeniería de datos | EE. UU. | Contratista por hora | KORE1, punto medio del pago al contratista: 97.50 USD/h | 97.50 |
| Ciencia de datos | EE. UU. | Contratista por hora | BLS nacional, mediana: 57.80 USD/h | 57.80 |
| IA / ML | EE. UU. | Contratista por hora | KORE1, punto medio del pago al contratista: 127.50 USD/h | 127.50 |
| DevOps | EE. UU. | Contratista por hora | KORE1, punto medio del pago al contratista: 77.50 USD/h | 77.50 |
| Diseño UX/UI | Latinoamérica | Contratista por hora | HiresLink, nivel medio: 3,200 USD/mes ÷ 173.3 h | 18.46 |
| Frontend | Latinoamérica | Contratista por hora | HiresLink, nivel medio: 4,000 USD/mes ÷ 173.3 h | 23.08 |
| Full-stack | Latinoamérica | Contratista por hora | HiresLink, nivel medio: 4,200 USD/mes ÷ 173.3 h | 24.23 |
| Móvil | Latinoamérica | Contratista por hora | HiresLink, nivel medio: 4,400 USD/mes ÷ 173.3 h | 25.38 |
| QA | Latinoamérica | Contratista por hora | HiresLink, nivel medio: 3,400 USD/mes ÷ 173.3 h | 19.62 |

- **Plantilla de Los Ángeles:** el salario es el 70 % de la compensación total (BLS ECEC), y su costo se reparte entre las horas facturables del año (el 66.4 % de SPI).
- **Contratistas:** cobran solo las horas trabajadas, más 49 USD al mes de Deel.

## 6. Costos laborales y facturación por profesional

Imprevistos del 10 % sobre las horas de cada profesional. La dedicación máxima es la de la semana más cargada, con un tope de 40 horas.

| Perfil | Ubicación | Horas base | Imprevistos | Horas totales | Dedicación media | Dedicación máxima | Costo/h | Costo | Tarifa al cliente | Facturado |
|---|---|---|---|---|---|---|---|---|---|---|
| Gestión de proyecto | Los Ángeles | 168 | 16.8 | 184.8 | 27 % | 49 % | 101.25 | 18,712 | 157.22 | 26,413 |
| Consultoría de RR. HH. | Los Ángeles | 80 | 8.0 | 88.0 | 13 % | 22 % | 90.97 | 8,005 | 141.24 | 11,299 |
| Liderazgo técnico | Los Ángeles | 144 | 14.4 | 158.4 | 23 % | 37 % | 150.45 | 23,832 | 233.60 | 33,638 |
| Backend | EE. UU. | 208 | 20.8 | 228.8 | 34 % | 58 % | 65.00 | 14,872 | 100.92 | 20,991 |
| Ingeniería de datos | EE. UU. | 48 | 4.8 | 52.8 | 8 % | 12 % | 97.50 | 5,148 | 151.39 | 7,267 |
| Ciencia de datos | EE. UU. | 40 | 4.0 | 44.0 | 6 % | 14 % | 57.80 | 2,543 | 89.74 | 3,590 |
| IA / ML | EE. UU. | 152 | 15.2 | 167.2 | 25 % | 41 % | 127.50 | 21,318 | 197.97 | 30,091 |
| DevOps | EE. UU. | 80 | 8.0 | 88.0 | 13 % | 20 % | 77.50 | 6,820 | 120.33 | 9,626 |
| Diseño UX/UI | Latinoamérica | 112 | 11.2 | 123.2 | 18 % | 39 % | 18.46 | 2,274 | 28.66 | 3,210 |
| Frontend | Latinoamérica | 88 | 8.8 | 96.8 | 14 % | 30 % | 23.08 | 2,234 | 35.83 | 3,153 |
| Full-stack | Latinoamérica | 40 | 4.0 | 44.0 | 6 % | 14 % | 24.23 | 1,066 | 37.62 | 1,505 |
| Móvil | Latinoamérica | 248 | 24.8 | 272.8 | 40 % | 69 % | 25.38 | 6,925 | 39.41 | 9,774 |
| QA | Latinoamérica | 136 | 13.6 | 149.6 | 22 % | 38 % | 19.62 | 2,934 | 30.46 | 4,143 |
| **Total** | | **1,544** | **154.4** | **1,698.4** | | | **68.70** | **116,683** | | **164,700** |

El resto de los honorarios, 63,426 USD, es la línea de gastos generales de la propuesta (sección 9).

## 7. Estado de resultados del proyecto

| Concepto | USD | % del precio |
|---|---|---|
| Honorarios | 228,126 | 98.4 % |
| Gastos reembolsables, facturados a coste | 3,675 | 1.6 % |
| **Precio total** | **231,801** | **100.0 %** |
| − Costo del equipo | 116,683 | 50.3 % |
| − Plataforma de contratistas (10 × 4 meses × 49 USD) | 1,960 | 0.8 % |
| − Gastos reembolsables | 3,675 | 1.6 % |
| **= Margen bruto** | **109,483** | **47.2 %** |
| − Gastos generales fijos (12.15 USD por hora del proyecto) | 20,639 | 8.9 % |
| − Marketing y ventas (8 % de los honorarios) | 18,250 | 7.9 % |
| **= Utilidad operativa** | **70,594** | **30.5 %** |
| − Impuesto de California para S corporation (1.5 %) | 1,059 | 0.5 % |
| **= Utilidad neta** | **69,535** | **30.0 %** |

**Gastos reembolsables, a coste:**

| Gasto | Cantidad | Costo unitario | Importe |
|---|---|---|---|
| Viajes a dos canteras en el descubrimiento y el piloto: 4 viajes de 150 millas a la tarifa del IRS | 600 millas | 0.725 USD | 435 |
| Traducción profesional al español de la interfaz de la app y de las encuestas | 6,000 palabras | 0.14 USD | 840 |
| Tabletas de prueba resistentes para el piloto | 2 dispositivos | 400 USD | 800 |
| Entornos de desarrollo y pruebas en la nube | 4 meses | 400 USD | 1,600 |
| **Total** | | | **3,675** |

## 8. Precio frente al mercado

La tarifa media del proyecto es de 134.32 USD por hora con imprevistos, un 10.5 % por debajo de los 150 USD/h que cobra una consultora pequeña.

| Concepto | Precio con margen del 30 % | Precio de mercado (150 USD/h) |
|---|---|---|
| Precio total | 231,801 | 258,435 |
| Utilidad neta | 69,535 | 93,671 |
| Margen neto | 30.0 % | 36.2 % |

## 9. Conciliación con la propuesta al cliente

Cada concepto de la propuesta lleva su costo, un 10 % de imprevistos y un recargo de rentabilidad del 45.3 % sobre el costo, el que hace que el proyecto deje un margen neto del 30.0 % sobre el precio. Es decir, costo × 1.5527. El cliente solo ve el valor final de cada concepto.

| Concepto | Costo base | Imprevistos (10 %) | Rentabilidad (45.3 %) | Valor en la propuesta |
|---|---|---|---|---|
| Gestión de proyecto: 168 h × 157.22 USD/h | 17,011 | 1,701 | 7,701 | 26,413 |
| Consultoría de RR. HH.: 80 h × 141.24 USD/h | 7,277 | 728 | 3,294 | 11,299 |
| Liderazgo técnico: 144 h × 233.60 USD/h | 21,665 | 2,166 | 9,807 | 33,638 |
| Backend: 208 h × 100.92 USD/h | 13,520 | 1,352 | 6,119 | 20,991 |
| Ingeniería de datos: 48 h × 151.39 USD/h | 4,680 | 468 | 2,119 | 7,267 |
| Ciencia de datos: 40 h × 89.74 USD/h | 2,312 | 231 | 1,047 | 3,590 |
| IA / ML: 152 h × 197.97 USD/h | 19,380 | 1,938 | 8,773 | 30,091 |
| DevOps: 80 h × 120.33 USD/h | 6,200 | 620 | 2,806 | 9,626 |
| Diseño UX/UI: 112 h × 28.66 USD/h | 2,068 | 207 | 935 | 3,210 |
| Frontend: 88 h × 35.83 USD/h | 2,031 | 203 | 919 | 3,153 |
| Full-stack: 40 h × 37.62 USD/h | 969 | 97 | 439 | 1,505 |
| Móvil: 248 h × 39.41 USD/h | 6,295 | 630 | 2,849 | 9,774 |
| QA: 136 h × 30.46 USD/h | 2,668 | 267 | 1,208 | 4,143 |
| Gastos generales del proyecto | 40,849 | 4,085 | 18,492 | 63,426 |
| Gastos reembolsables, a coste | 3,675 | 0 | 0 | 3,675 |
| **Total** | **150,600** | **14,693** | **66,508** | **231,801** |

Los gastos generales del proyecto son la plataforma de contratistas (1,960), los gastos fijos asignados (20,639) y el marketing (18,250). Su valor en la propuesta absorbe el redondeo al dólar de las tarifas, para que todo sume exactamente el precio.

## 10. Margen de negociación

| Margen neto | Honorarios | Precio total | Descuento sobre el precio propuesto |
|---|---|---|---|
| 30.0 % (propuesta) | 228,126 | 231,801 | — |
| 25 % | 210,472 | 214,147 | 7.6 % |
| 20 % | 195,310 | 198,985 | 14.2 % |
| 10 % | 170,628 | 174,303 | 24.8 % |
| 0 % (equilibrio) | 151,393 | 155,068 | 33.1 % |

Por debajo de 155,068 USD, un descuento del 33.1 %, el proyecto pierde dinero.

## 11. Sensibilidad a las horas

El precio es cerrado: si se trabajan más horas, se pagan del margen. Los gastos fijos asignados crecen con las horas.

| Escenario | Horas | Costo del equipo | Utilidad neta | Margen neto |
|---|---|---|---|---|
| Sin usar los imprevistos | 1,544.0 | 106,075 | 81,832 | 35.3 % |
| Presupuesto, con todos los imprevistos | 1,698.4 | 116,683 | 69,535 | 30.0 % |
| Un 10 % más de horas que el presupuesto | 1,868.2 | 128,351 | 56,009 | 24.2 % |
| Un 20 % más de horas que el presupuesto | 2,038.1 | 140,020 | 42,482 | 18.3 % |

Si las horas superan el presupuesto en más de un 17.1 %, el margen baja del 20 %; con un 51.4 % más, la utilidad llega a cero.

## 12. Plan de facturación y cobro

| Hito | Momento | % de los honorarios | Importe | Mes en que se espera el cobro |
|---|---|---|---|---|
| 1 | A la firma del contrato | 25 % | 57,032 | 1 |
| 2 | Al terminar la etapa 1, «Descubrimiento y diseño» (semana 3) | 25 % | 57,032 | 3 |
| 3 | Al terminar la etapa 2, «Construcción» (semana 11) | 25 % | 57,032 | 5 |
| 4 | Al cierre del proyecto (semana 17) | 25 % | 57,030 | 6 |

El anticipo se cobra al firmar; el resto de los hitos y los gastos reembolsables, que se facturan a fin de mes, se cobran a 45 días.

## 13. Flujo de caja mensual

| Mes | Cobros | Pagos | Neto | Acumulado |
|---|---|---|---|---|
| 1 | 57,032 | 38,029 | 19,003 | 19,003 |
| 2 | 0 | 56,573 | -56,573 | -37,570 |
| 3 | 57,897 | 36,966 | 20,931 | -16,639 |
| 4 | 1,081 | 29,638 | -28,557 | -45,196 |
| 5 | 57,897 | 0 | 57,897 | 12,701 |
| 6 | 57,895 | 0 | 57,895 | 70,596 |
| **Caja máxima que hay que adelantar** | | | | **45,196** |

- **Pagos:** el equipo se paga según el cronograma semanal (sección 14); la plataforma, los gastos fijos, el marketing y los gastos reembolsables, por igual cada semana.
- **Impuesto:** el de California se paga una vez al año y no entra en el flujo mensual.

## 14. Línea base de seguimiento semanal

Horas planificadas de cada perfil, con imprevistos, y costo acumulado del equipo. Sirve para comparar cada semana lo real con lo previsto.

| Semana | Etapa | Gestión de proyecto | Consultoría de RR. HH. | Liderazgo técnico | Backend | Ingeniería de datos | Ciencia de datos | IA / ML | DevOps | Diseño UX/UI | Frontend | Full-stack | Móvil | QA | Horas | Costo del equipo | Acumulado | % del costo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 15.0 | 8.8 | 14.8 | 5.6 | 4.8 | 0.0 | 0.0 | 8.0 | 15.5 | 0.0 | 0.0 | 0.0 | 0.0 | 72.5 | 6,286 | 6,286 | 5 % |
| 2 | 1 | 15.0 | 8.8 | 14.8 | 5.6 | 4.8 | 0.0 | 0.0 | 8.0 | 15.5 | 0.0 | 0.0 | 0.0 | 0.0 | 72.5 | 6,286 | 12,572 | 11 % |
| 3 | 1 | 15.0 | 8.8 | 14.8 | 5.6 | 4.8 | 0.0 | 0.0 | 8.0 | 15.5 | 0.0 | 0.0 | 0.0 | 0.0 | 72.5 | 6,286 | 18,858 | 16 % |
| 4 | 2 | 6.2 | 2.2 | 8.9 | 23.2 | 4.8 | 5.5 | 16.5 | 8.0 | 9.6 | 12.1 | 5.5 | 27.5 | 11.0 | 141.1 | 8,695 | 27,553 | 24 % |
| 5 | 2 | 6.2 | 2.2 | 8.9 | 23.2 | 4.8 | 5.5 | 16.5 | 8.0 | 9.6 | 12.1 | 5.5 | 27.5 | 11.0 | 141.1 | 8,695 | 36,249 | 31 % |
| 6 | 2 | 6.2 | 2.2 | 8.9 | 23.2 | 4.8 | 5.5 | 16.5 | 8.0 | 9.6 | 12.1 | 5.5 | 27.5 | 11.0 | 141.1 | 8,695 | 44,944 | 39 % |
| 7 | 2 | 6.2 | 2.2 | 8.9 | 23.2 | 4.8 | 5.5 | 16.5 | 8.0 | 9.6 | 12.1 | 5.5 | 27.5 | 11.0 | 141.1 | 8,695 | 53,640 | 46 % |
| 8 | 2 | 6.2 | 2.2 | 8.9 | 23.2 | 4.8 | 5.5 | 16.5 | 8.0 | 9.6 | 12.1 | 5.5 | 27.5 | 11.0 | 141.1 | 8,695 | 62,335 | 53 % |
| 9 | 2 | 6.2 | 2.2 | 8.9 | 23.2 | 4.8 | 5.5 | 16.5 | 8.0 | 9.6 | 12.1 | 5.5 | 27.5 | 11.0 | 141.1 | 8,695 | 71,031 | 61 % |
| 10 | 2 | 6.2 | 2.2 | 8.9 | 23.2 | 4.8 | 5.5 | 16.5 | 8.0 | 9.6 | 12.1 | 5.5 | 27.5 | 11.0 | 141.1 | 8,695 | 79,726 | 68 % |
| 11 | 2 | 6.2 | 2.2 | 8.9 | 23.2 | 4.8 | 5.5 | 16.5 | 8.0 | 9.6 | 12.1 | 5.5 | 27.5 | 11.0 | 141.1 | 8,695 | 88,422 | 76 % |
| 12 | 3 | 12.8 | 6.6 | 8.5 | 0.0 | 0.0 | 0.0 | 6.6 | 0.0 | 0.0 | 0.0 | 0.0 | 8.8 | 15.4 | 58.8 | 4,550 | 92,971 | 80 % |
| 13 | 3 | 12.8 | 6.6 | 8.5 | 0.0 | 0.0 | 0.0 | 6.6 | 0.0 | 0.0 | 0.0 | 0.0 | 8.8 | 15.4 | 58.8 | 4,550 | 97,521 | 84 % |
| 14 | 3 | 12.8 | 6.6 | 8.5 | 0.0 | 0.0 | 0.0 | 6.6 | 0.0 | 0.0 | 0.0 | 0.0 | 8.8 | 15.4 | 58.8 | 4,550 | 102,070 | 87 % |
| 15 | 3 | 12.8 | 6.6 | 8.5 | 0.0 | 0.0 | 0.0 | 6.6 | 0.0 | 0.0 | 0.0 | 0.0 | 8.8 | 15.4 | 58.8 | 4,550 | 106,620 | 91 % |
| 16 | 4 | 19.4 | 8.8 | 4.1 | 13.2 | 0.0 | 0.0 | 4.4 | 0.0 | 0.0 | 0.0 | 0.0 | 8.8 | 0.0 | 58.8 | 5,031 | 111,652 | 96 % |
| 17 | 4 | 19.4 | 8.8 | 4.1 | 13.2 | 0.0 | 0.0 | 4.4 | 0.0 | 0.0 | 0.0 | 0.0 | 8.8 | 0.0 | 58.8 | 5,031 | 116,683 | 100 % |

## 15. Alertas para el seguimiento

- **Reserva de imprevistos:** 154.4 horas, unos 10,608 USD de costo. Si en la semana 9 ya se ha consumido más de la mitad, hay que revisar el alcance con el cliente.
- **Horas por perfil:** avisar cuando un perfil supere sus horas base (sección 6): desde ahí consume imprevistos, y al pasar sus horas totales consume margen.
- **Costo acumulado:** si el costo real supera en más de un 5 % al de la línea base dos semanas seguidas, hay que replanificar.
- **Margen:** con un 17.1 % más de horas que el presupuesto, el margen baja del 20 %; con un 51.4 % más, el proyecto pierde dinero.
- **Cobros:** si un hito no se cobra a los 45 días, la caja que hay que adelantar crece en su importe.

## 16. Peso del proyecto en la empresa

| Concepto | Proyecto | Empresa en un año | % |
|---|---|---|---|
| Horas facturables | 1,698.4 | 22,098 | 7.7 % |
| Gastos generales fijos absorbidos | 20,639 | 268,534 | 7.7 % |
| Honorarios | 228,126 | 2,947,421 | 7.7 % |

**Mezcla del equipo por ubicación:**

| Ubicación | Horas totales | % de las horas | Costo | % del costo |
|---|---|---|---|---|
| Los Ángeles | 431.2 | 25.4 % | 50,549 | 43.3 % |
| EE. UU. | 580.8 | 34.2 % | 50,701 | 43.5 % |
| Latinoamérica | 686.4 | 40.4 % | 15,433 | 13.2 % |

## 17. Controles de coherencia

- ✅ El margen neto es del 30.0 %, el objetivo de la empresa.
- ✅ La tarifa media, 134.32 USD por hora con imprevistos, no pasa de 150 USD/h.
- ⚠️ La tarifa media queda un 10.5 % por debajo del mercado. Cobrando 150 USD/h, la utilidad neta subiría a 93,671 USD (margen del 36.2 %): fijar el precio por el margen objetivo deja ese dinero en la mesa.
- ✅ Nadie pasa del 100 % de dedicación en ninguna semana. La más alta es la de Móvil, con un 69 %.
- ⚠️ La reunión dejó 3 puntos de alcance sin decidir, que no están estimados (sección 2). Decide qué entra y vuelve a estimar indicando los cambios de alcance.
- ✅ La propuesta al cliente suma exactamente el precio total: 231,801 USD.
- ✅ Los cuatro hitos de pago suman exactamente los honorarios.
- ✅ Todas las tarifas al cliente cubren el costo de su perfil y sus imprevistos.
- ⚠️ Tarifas fuera del rango de 75-175 USD/h de las consultoras pequeñas (Cleveroad): Liderazgo técnico 233.60, IA / ML 197.97, Diseño UX/UI 28.66, Frontend 35.83, Full-stack 37.62, Móvil 39.41, QA 30.46. Las más bajas pueden dejar ver que ese perfil trabaja desde un país de menor costo; las más altas invitan a negociar.
- ⚠️ Un margen neto del 30 % es alto: más del doble de la media de las agencias pequeñas (12 %), aunque dentro del 25-40 % de las especializadas (Promethean, vía Haus Advisors). Es alcanzable sobre todo porque los contratistas solo cobran las horas trabajadas.
- ℹ️ La empresa adelanta hasta 45,196 USD de caja antes de cobrar los hitos que faltan.

## 18. Riesgos para la consultora

- Si el contenido de la formación no llega a tiempo, el piloto se retrasa y la temporada de contratación de marzo a junio queda sin cubrir: conviene pedir el contenido ya en el descubrimiento.
- El asistente puede dar respuestas incorrectas o incompletas sobre seguridad. Hace falta un conjunto de preguntas de evaluación revisado por EHS antes del piloto, y el cliente debe aceptar que el supervisor siempre tiene la última palabra.
- Los unos 40 manuales pueden estar desactualizados, duplicados o en formatos difíciles de leer: la ingesta puede necesitar más horas.
- La cobertura muy mala en varias canteras puede alargar las pruebas de sincronización y el piloto.
- Calendario de 17 semanas para cerrar antes de la temporada: un retraso en la revisión de MSHA o en el acceso al HRIS lo mueve todo.
- Las distancias de los viajes son supuestos, porque la reunión no las dio: se confirman en el descubrimiento.
- Existen plataformas SaaS de formación MSHA. El desarrollo se justifica por el registro en tablet sin conexión, el asistente con los manuales propios y el panel por cantera: conviene compararlo en el descubrimiento.
