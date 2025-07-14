# Desafío Técnico (72 h)

# Agente Conversacional “Scraper + LangChain”

## 1. Contexto

Assetplan mantiene diversos agentes conversacionales para diferentes áreas de la empresa.
Uno de ellos se enfoca en responder consultas sobre propiedades disponibles, recomendar,
etc. Te invitamos a recrear uno de nuestros agentes conversacionales actualmente activos. El
**agente conversacional** debe ser capaz de:

1. **Rastrear (scrapear)** datos de propiedades desde assetplan.cl
2. **Generar una base vectorial estructurada** con los atributos clave (precio, ubicación,
    m², n.º habitaciones, url, links de fotos, etc).
3. **Responder en lenguaje natural** preguntas de usuarios (“¿Qué departamentos de 2
    dormitorios hay en Providencia bajo 3 000 UF?”) con información fresca, citando la
    fuente.
4. **Debe tener una forma de probarlo** , ya sea por línea de comando u otro.
5. **Puedes utilizar IAs (codex, jules, copilot, etc)** , pero en la entrevista post desafío
    deberás ser capaz de responder qué hace cada parte del código

## 2. Objetivos obligatorios

```
Nº Entregable Detalle
1 Scraper
reproducible
Usa BeatifulSoap, Playwright, Selenium o similar para extraer al
menos 50 propiedades desde assetplan.cl. El código debe poder
ejecutarse con un comando (make scrape o npm script) y
guardar los datos en un JSON o SQLite.
2 Knowledge
Base +
LangChain
Carga los datos al índice/VectorStore que prefieras (ChromaDB,
FAISS, OpenSearch...). Implementa un agent o RAG chain en
LangChain que conteste preguntas sobre las propiedades,
citando la URL original.
3 API o CLI Expón el agente vía REST, FastAPI, Lambda o un CLI interactivo.
Debe aceptar preguntas y devolver respuestas JSON (answer,
sources, confidence).
```

```
4 Tests Incluye pruebas automáticas que validen: scraping mínimo,
inserción en el store y respuesta correcta a 2-3 queries estándar.
5 README y
Diagrama
Explica cómo correr el scraper, levantar el agente y ejecutar los
tests. Aporta un diagrama simple (Mermaid o imagen).
6 Límite de
tiempo
Tu solución debe instalarse desde cero y entregar la primera
respuesta en < 60 s en un equipo t3.medium o equivalente.
```
## 3. Requisitos técnicos

```
● Lenguaje : Python 3.13 (utiliza uv) y/o TypeScript (utiliza yarn) si lo prefieres para el
scraper o lambda handlers.
● Framework : LangChain > 0.3.
● Infra opcional : Docker, AWS Lambda/API Gateway, Terraform (bonus).
● Estilo : código claro, tipado con typing/TypeScript strict, en Python utilizando
pydantic. comentarios concisos.
```
## 4. Bonus (puntos extra)

```
+ Descripción
★ Utilizar servicios de AWS (lambda, EC2, etc).
★ Actualización incremental (detectar cambios en precio y avisar).
★ Manejo de logs via Grafana/Loki o CloudWatch que registre preguntas y latencia.
★ Manejo multilingüe (es-en) con detección automática.
★ Infra como código (Terraform/CDK) y pipeline CI/CD GitHub Actions.
```
## 5. Evaluación

```
Criterio Peso
Calidad de código (claridad, modularidad, tests) 40 %
Cobertura funcional (scraping, agent, API) 30 %
```

```
Escalabilidad y rendimiento 10 %
Documentación y DX 10 %
Creatividad/bonus 10 %
```
## 6. Entrega

1. **Repositorio Git** público o privado (otorgando acceso al usuario github.com/patcornejo)
    con:
       ○ Código fuente, requirements.txt/poetry.lock o package.json.
       ○ Dockerfile / Terraform si aplica.
       ○ README y diagrama.
    **** Importante** : Debe poder ejecutarse el proyecto sólo leyendo el README.
2. Enviar el link del repo vía correo electrónico antes de que se cumplan **72 h** desde la
    hora de recepción.

## 7. Recursos útiles

● LangChain docs: https://python.langchain.com/
● ChromaDB quick-start: https://docs.trychroma.com/
● Ejemplo Agent + Tools: https://python.langchain.com/docs/how_to/#agents
¡Éxito! Cualquier duda técnica, a través de correo electrónico o get on board.



