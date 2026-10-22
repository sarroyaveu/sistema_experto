# 🧠 NEXUS Expert: Sistema Experto en Informática

Sistema experto con motor de inferencia por **encadenamiento hacia adelante** y **resolución de conflictos**.
Un único motor sirve a tres dominios, cada uno con su base de conocimiento en JSON:

| Dominio | Entrada del usuario | Salida |
|---|---|---|
| 🛡️ Ciberseguridad | Alertas observadas | Diagnóstico y acciones a tomar |
| ☁️ Arquitectura en la nube | Requisitos del sistema | Arquitectura recomendada |
| 🤖 Modelos de IA | Necesidades y restricciones | Modelo de IA a desplegar |

## Integrante
- SALOMÉ ARROYAVE URREA

## Instalación
```bash
git clone <URL_DEL_REPOSITORIO>
cd sistema_experto
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Dependencias
- Python 3.9 o superior
- streamlit (interfaz web)

## Ejecución
```bash
streamlit run app.py          # interfaz gráfica
python engine.py knowledge_base/nube.json examples/caso_nube.json   # prueba por consola
```

## Estructura de carpetas
```
├── app.py                 # Interfaz (Streamlit)
├── engine.py              # Motor de inferencia y cargadores
├── knowledge_base/        # Bases de conocimiento (JSON), una por dominio
├── examples/              # Casos de ejemplo (hechos iniciales en JSON)
├── docs/                  # Documento técnico
├── .streamlit/config.toml # Tema visual
└── requirements.txt
```

## Formato de la base de conocimiento
- `hechos`: catálogo con `texto`, `tipo` (`entrada`, `intermedio`, `recomendacion`), `grupo` y `detalle` (solo recomendaciones).
- `reglas`: `id`, `nombre`, `antecedentes`, `consecuentes`, `prioridad` (opcional) y `excluye` (opcional, solo reglas de recomendación).

## Formato de los hechos iniciales
`{"hechos": ["hecho_a", "hecho_b"]}`, o bien una lista, o un diccionario `{hecho: true/false}`.

## Estrategia de resolución de conflictos
1. Refracción (no repetir reglas y descartar las que no aportan hechos nuevos)
2. Fases: inferencia primero, recomendación después
3. Prioridad explícita (salience)
4. Recencia
5. Especificidad
6. Orden de definición

Referentes: McDermott y Forgy (1978); Forgy, OPS5 (1981); Giarratano y Riley, *Expert Systems*; Russell y Norvig, *AIMA*.

## Uso de IA generativa
Se utilizó IA generativa como apoyo en el diseño y la codificación. Ver detalle en `docs/`.