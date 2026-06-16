# GUÍA DE REFERENCIA RÁPIDA - MÓDULOS

## Localización de Funciones

### 🗄️ Database (`src/app/database/`)

| Función | Módulo | Importar |
|---------|--------|----------|
| `obtener_conexion()` | `connection.py` | `from src.app.database import obtener_conexion` |

---

### 📧 Services - Email (`src/app/services/`)

| Función | Módulo | Importar | Nota |
|---------|--------|----------|------|
| `enviar_correo(app, nombre, token, correo)` | `email_service.py` | `from src.app.services import enviar_correo` | Requiere instancia Flask |

---

### 📝 Services - Posts (`src/app/services/`)

| Función | Módulo | Importar |
|---------|--------|----------|
| `salvar_post(post_id=None)` | `post_service.py` | `from src.app.services import salvar_post` |
| `agrupar_filas_posts(resultados)` | `post_service.py` | `from src.app.services import agrupar_filas_posts` |

---

### 💬 Services - Comments (`src/app/services/`)

| Función | Módulo | Importar |
|---------|--------|----------|
| `salvar_comentario(comentario_id=None, post_id=None)` | `comment_service.py` | `from src.app.services import salvar_comentario` |

---

### 📂 Storage (`src/app/storage/`)

| Función | Módulo | Importar |
|---------|--------|----------|
| `allowed_file(filename)` | `files.py` | `from src.app.storage import allowed_file` |
| `borrar_archivos(id)` | `files.py` | `from src.app.storage import borrar_archivos` |
| `extraer_archivo(fila)` | `files.py` | `from src.app.storage import extraer_archivo` |

---

### 🔐 Utils - Security (`src/app/utils/`)

| Función | Módulo | Importar |
|---------|--------|----------|
| `generar_token()` | `security.py` | `from src.app.utils import generar_token` |
| `calcular_retraso_exponencial(intentos)` | `security.py` | `from src.app.utils import calcular_retraso_exponencial` |

---

### 📄 Utils - Text (`src/app/utils/`)

| Función | Módulo | Importar |
|---------|--------|----------|
| `limpiar_contenido(contenido)` | `text.py` | `from src.app.utils import limpiar_contenido` |

---

### 📊 Utils - Pagination (`src/app/utils/`)

| Función | Módulo | Importar |
|---------|--------|----------|
| `generar_paginas(pagina_actual, total_paginas, rango=2)` | `pagination.py` | `from src.app.utils import generar_paginas` |
| `obtener_datos_paginados(cursor, ...)` | `pagination.py` | `from src.app.utils import obtener_datos_paginados` |

---

### ⚙️ Config (`src/app/`)

| Constante | Módulo | Importar |
|-----------|--------|----------|
| `MAX_INTENTOS` | `config.py` | `from src.app import MAX_INTENTOS` |
| `TIEMPO_BLOQUEADO` | `config.py` | `from src.app import TIEMPO_BLOQUEADO` |
| `TIEMPO_TOKEN` | `config.py` | `from src.app import TIEMPO_TOKEN` |
| `RETRASO_BASE` | `config.py` | `from src.app import RETRASO_BASE` |
| `POSTS_POR_PAGINA` | `config.py` | `from src.app import POSTS_POR_PAGINA` |
| `UPLOAD_FOLDER` | `config.py` | `from src.app import UPLOAD_FOLDER` |
| `ALLOWED_EXTENSIONS` | `config.py` | `from src.app import ALLOWED_EXTENSIONS` |

---

## Ejemplos de Uso

### Importar desde app principal
```python
from src.app import (
    obtener_conexion,
    salvar_post,
    generar_token,
    POSTS_POR_PAGINA
)
```

### Importar de módulos específicos
```python
from src.app.database import obtener_conexion
from src.app.services import salvar_post, salvar_comentario
from src.app.utils import generar_token, limpiar_contenido
from src.app.storage import allowed_file
```

### Importar en app.py actual
```python
# app.py ya tiene todos importados:
from src.app import (
    obtener_conexion,
    enviar_correo,
    salvar_post,
    agrupar_filas_posts,
    salvar_comentario,
    allowed_file,
    borrar_archivos,
    extraer_archivo,
    generar_token,
    calcular_retraso_exponencial,
    limpiar_contenido,
    generar_paginas,
    obtener_datos_paginados,
    MAX_INTENTOS,
    TIEMPO_BLOQUEADO,
    TIEMPO_TOKEN,
    RETRASO_BASE,
    POSTS_POR_PAGINA,
    UPLOAD_FOLDER,
    ALLOWED_EXTENSIONS,
)
```

---

## Diagrama de Dependencias

```
app.py
  ├── src.app.database
  │   └── obtener_conexion()
  │
  ├── src.app.services
  │   ├── email_service (enviar_correo)
  │   ├── post_service (salvar_post, agrupar_filas_posts)
  │   │   └── Depende: storage, utils
  │   └── comment_service (salvar_comentario)
  │       └── Depende: utils
  │
  ├── src.app.storage
  │   └── files (allowed_file, borrar_archivos, extraer_archivo)
  │       └── Depende: database, config
  │
  └── src.app.utils
      ├── security (generar_token, calcular_retraso_exponencial)
      ├── text (limpiar_contenido)
      └── pagination (generar_paginas, obtener_datos_paginados)
```

---

## Cambios en app.py

**Línea ~266:** Actualización de llamada a `enviar_correo()`

❌ **Antes:**
```python
enviar_correo(nombre_usuario, token, correo)
```

✅ **Ahora:**
```python
enviar_correo(app, nombre_usuario, token, correo)
```

---

**Creado:** 2026-06-14  
**Versión:** 1.0
