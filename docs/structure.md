# 🛠️ Mapa de Arquitectura y Estructura — Filmopibes

Este documento contiene la estructura interna completa del proyecto, reflejando la organización del backend (FastAPI) y del frontend (React + Vite + Tailwind CSS).

---

## 🌳 1. Estructura Global del Repositorio

```text
D:\PROYECTOSGIT\FILMOPIBES
│
├── .gitattributes
├── .gitignore
├── LICENSE
├── peliculas_sin_genero.txt    # Registro de películas que requirieron auditoría manual.
├── README.md                   # Documentación general pública para el repositorio.
├── DOCUMENTACION_TECNICA.md    # Manual interno de arquitectura y estructura.
│
├── backend/                    # NÚCLEO DEL BACKEND (FastAPI + MongoDB)
│   ├── .env                    # Variables secretas (MONGO_URI, passAPIMovieDB, OMDB_API_KEY, JWT_SECRET).
│   ├── .env.example            # Plantilla de variables de entorno para versión controlada.
│   ├── requirements.txt        # Dependencias (fastapi, uvicorn, motor, pymongo, pydantic...).
│   │
│   ├── Filmoteca.csv           # Fuente de datos histórica original.
│   ├── Filmoteca.xlsx          # Hoja de cálculo original de referencia.
│   │
│   ├── categorizingFilmsMongoDB.py  # Script de asignación masiva de géneros y décadas.
│   ├── platformEsp.py          # Enriquecimiento de plataformas de streaming en España.
│   ├── fixAlien.py             # Corrección puntual de IDs de TMDB en sagas.
│   ├── fixMongoDB.py           # Normalización de colecciones e índices iniciales.
│   ├── revisaduplicados.py     # Script de auditoría y resolución atómica de duplicados.
│   │
│   └── app/                    # MÓDULO PRINCIPAL DE LA APLICACIÓN PYTHON
│       ├── __init__.py         # Paquete ejecutable de Python.
│       ├── database.py         # Conexión asíncrona con MongoDB mediante Motor.
│       ├── main.py             # Instancia FastAPI, middleware CORS y ciclo de vida (Lifespan).
│       ├── models.py           # Modelos Pydantic v2 (PeliculaGridItem, ValoracionUpsertRequest).
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   └── settings.py     # Gestor de configuración y variables de entorno.
│       │
│       └── routers/            # ENDPOINTS DE LA API REST
│           ├── __init__.py
│           ├── films.py        # Obtenedor del grid agrupado y CRUD de películas.
│           ├── users.py        # Gestión y autenticación de usuarios.
│           └── ratings.py      # Upsert atómico de valoraciones, notas y flags.
│
└── frontend/                   # APLICACIÓN CLIENTE (React + Vite + Tailwind CSS)
    ├── api/                        # Capa de red / Comunicación HTTP
    │   ├── axiosClient.js          # Instancia base de Axios con baseURL ([http://127.0.0.1:8000](http://127.0.0.1:8000)).
    │   └── peliculasApi.js         # Funciones API: getGridPeliculas(), upsertValoracion().
    │
    ├── components/                 # Componentes de la interfaz
    │   ├── common/                 # Componentes generales
    │   │   ├── Navbar.jsx          # Barra de navegación superior y conmutador de usuario.
    │   │   ├── SearchBar.jsx       # Buscador dinámico por título/director.
    │   │   └── StatsSummary.jsx    # Métricas clave (películas vistas, notas medias, total).
    │   │
    │   ├── grid/                   # Módulo principal Data Grid (Vista tipo Excel)
    │   │   ├── FilmGrid.jsx        # Componente contenedor montado con TanStack Table.
    │   │   ├── EditableCell.jsx    # Celda interactiva (Checkbox de vistas, Input numérico).
    │   │   ├── PosterCell.jsx      # Miniatura del cartel con vista previa flotante.
    │   │   └── ColumnHeaders.jsx   # Cabeceras de columna con ordenación y filtros.
    │   │
    │   └── modals/                 # Ventanas emergentes y paneles
    │       ├── FilmDetailModal.jsx # Vista detallada de la película y sinopsis inviolable.
    │       └── AddFilmModal.jsx    # Formulario para incorporar nuevas películas desde TMDB.
    │
    ├── context/                    # Estado global ligero
    │   └── UserContext.jsx         # Contexto de autenticación para el usuario activo (Manolo / Jotace).
    │
    ├── hooks/                      # Custom Hooks reutilizables
    │   └── usePeliculasGrid.js     # Gestión del estado de la tabla mediante React Query.
    │
    ├── utils/                      # Utilidades y constantes
    │   ├── formatters.js           # Formateadores (escala de colores para notas, fechas).
    │   └── constants.js            # Mapeos estáticos (plataformas, géneros, badges).
    │
    ├── App.jsx                     # Componente raíz (Orquestador de Layout + Modales).
    ├── main.jsx                    # Punto de montaje de React en el DOM.
    └── index.css                   # Importación de directivas de Tailwind CSS.