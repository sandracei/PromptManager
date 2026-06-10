# 📚 Biblioteca de Prompts — con SharePoint

## 🚀 Cómo arrancar

### 1. Instala las dependencias (solo la primera vez)
```bash
pip install -r requirements.txt
```

### 2. Arranca la app
```bash
streamlit run app.py
```

---

## 🔐 Primer inicio de sesión

La primera vez que arranques la app (y cuando el token expire, aprox. cada 90 días):

1. La app te mostrará un **código de 9 caracteres** y un enlace
2. Abre [https://microsoft.com/devicelogin](https://microsoft.com/devicelogin)
3. Introduce el código
4. Inicia sesión con tu **cuenta de empresa**
5. Vuelve a la app y pulsa **"Verificar sesión"**

El token se guarda en `.msal_token_cache.json` (en la misma carpeta). Cada compañero tiene el suyo.
⚠️ No compartas ese archivo con nadie.

---

## 📁 Archivos del proyecto

```
prompt_library/
├── app.py                    ← La aplicación
├── sharepoint_helper.py      ← Módulo de conexión a SharePoint
├── requirements.txt          ← Dependencias
├── README.md                 ← Este archivo
├── .msal_token_cache.json    ← Se crea automáticamente (no compartir)
└── prompts_ejemplo.csv       ← Ejemplo para importar
```

El archivo `prompts.csv` vive en SharePoint, en la carpeta:
`/OOEU Workstream/Support Chatbot/Operational/04.1 PromptManager/`

---

## ✨ Funcionalidades

| Sección | Qué puedes hacer |
|---|---|
| 🏠 Inicio | Buscar, filtrar, leer prompts. Ver historial. Editar o desactivar. |
| ➕ Añadir prompt | Crear nuevo o nueva versión (versionado automático). |
| 📤 Importar archivo | Subir prompts desde `.txt`, `.csv` o `.xlsx`. |
| 📥 Exportar | Descargar en CSV o Excel (recientes o historial completo). |

---

## 📋 Formato para importar CSV/Excel

| Columna | Obligatoria |
|---|---|
| `nombre` | ✅ |
| `prompt` | ✅ |
| `descripcion` | ➖ |
| `categoria` | ➖ |
| `responsable` | ➖ |

---

## 💡 Consejos

- Pulsa **🔄 Recargar datos** en el menú si otra persona ha guardado cambios recientemente.
- Si alguien edita el CSV directamente en SharePoint, recarga para sincronizar.
- Los prompts con el mismo nombre se versionan automáticamente (v1.0 → v1.1…).
