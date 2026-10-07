# 🎬 Filmopibes

> Plataforma social privada para la gestión, valoración y catalogación de cine entre un grupo de amigos.

Filmopibes nace para cubrir la brecha entre el seguimiento social de películas (al estilo Letterboxd) y la integración con servidores multimedia locales (Plex/Jellyfin), manteniendo una arquitectura ligera, asíncrona y con coste cero de infraestructura.

---

## 🚀 Características Principales

- 🍿 **Catálogo Enriquecido:** Integración de metadatos, pósters, sinopsis y disponibilidad en plataformas de streaming.
- ⭐ **Interacción Social:** Control de películas vistas, calificaciones personales, seguimiento de rewatches y listas de *"Quiero Ver"*.
- 🔔 **Novedades Eficientes:** Sistema de notificación por fechas (`fecha_registro` vs `fecha_añadida`) que evita registros duplicados o fantasmas en la base de datos.
- 🔐 **Autenticación y Roles:** Control de acceso mediante tokens JWT (distinguiendo entre gestión de catálogo y usuarios estándar).
- ⚡ **Backend Asíncrono:** Desarrollado con **FastAPI** y **MongoDB** (Motor driver) para máxima velocidad de respuesta.

---

## 🛠️ Tecnologías

- **Backend:** Python, FastAPI, Motor (Async MongoDB), Pydantic v2, PyJWT, Passlib
- **Base de Datos:** MongoDB (Local / Atlas)
- **Frontend:** *(En desarrollo)*
- **Arquitectura:** Monorepo (`backend/` y `frontend/`)

---

## 📁 Estructura del Repositorio

```text
filmopibes/
├── backend/          # API REST con FastAPI
│   ├── app/          # Lógica de aplicación, modelos y routers
│   ├── .env.example  # Plantilla de variables de entorno
│   └── requirements.txt
├── frontend/         # Interfaz de usuario (En desarrollo)
├── .gitignore        # Reglas de exclusión para Git
├── LICENSE           # Licencia MIT
└── README.md         # Documentación principal
