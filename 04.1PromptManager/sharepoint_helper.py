"""
sharepoint_helper.py
Handles authentication and read/write of prompts.csv on SharePoint
using MSAL device-code flow (no app registration needed beyond the
well-known Microsoft Office client_id).
"""

import os
import json
import io
import pandas as pd
import msal
import requests
import streamlit as st

# ── SharePoint config ────────────────────────────────────────────────────────
SHAREPOINT_URL   = "https://corpdir.sharepoint.com"
SITE_PATH        = "/sites/DWT_OOEU"
FOLDER_PATH      = "/OOEU Workstream/Support Chatbot/Operational/04.1 PromptManager"
FILE_NAME        = "prompts.csv"
TOKEN_CACHE_FILE = ".msal_token_cache.json"

# Microsoft's well-known public client ID for Office apps
# (works for delegated auth without registering your own Azure app)
CLIENT_ID = "d3590ed6-52b3-4102-aeff-aad2292ab01c"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES    = ["https://corpdir.sharepoint.com/.default"]

COLUMNS = ["id", "nombre", "descripcion", "prompt", "version",
           "cambios", "responsable", "fecha", "categoria", "activo"]


# ── Token cache (persisted to disk) ─────────────────────────────────────────
def _build_msal_app():
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        cache.deserialize(open(TOKEN_CACHE_FILE).read())
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)
    return app, cache


def _save_cache(cache):
    if cache.has_state_changed:
        with open(TOKEN_CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def get_access_token():
    """Return a valid access token, triggering device-code login if needed."""
    app, cache = _build_msal_app()

    # Try silent first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            _save_cache(cache)
            return result["access_token"]

    # Device-code flow
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Error iniciando autenticación: {flow}")

    # Show instructions in Streamlit
    st.warning("🔐 **Inicio de sesión necesario**")
    st.markdown(f"""
    1. Abre [https://microsoft.com/devicelogin](https://microsoft.com/devicelogin) en el navegador
    2. Introduce el código: **`{flow['user_code']}`**
    3. Inicia sesión con tu cuenta de empresa
    4. Vuelve aquí y pulsa **Verificar sesión**
    """)
    st.code(flow['user_code'], language=None)

    if st.button("✅ Verificar sesión"):
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            _save_cache(cache)
            st.success("✅ Sesión iniciada correctamente. Recargando…")
            st.rerun()
        else:
            st.error(f"Error de autenticación: {result.get('error_description', result)}")
    st.stop()


# ── SharePoint REST helpers ──────────────────────────────────────────────────
def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json;odata=verbose",
    }


def _file_url(token):
    """Returns the REST URL for the CSV file."""
    encoded = requests.utils.quote(f"{FOLDER_PATH}/{FILE_NAME}")
    return f"{SHAREPOINT_URL}{SITE_PATH}/_api/web/GetFileByServerRelativeUrl('{SITE_PATH}{encoded}')"


def load_from_sharepoint():
    """Download prompts.csv from SharePoint and return a DataFrame."""
    token = get_access_token()
    url   = _file_url(token) + "/$value"
    resp  = requests.get(url, headers=_headers(token))

    if resp.status_code == 404:
        # File doesn't exist yet → return empty DataFrame
        return pd.DataFrame(columns=COLUMNS)
    resp.raise_for_status()

    df = pd.read_csv(io.StringIO(resp.content.decode("utf-8")))
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df


def save_to_sharepoint(df: pd.DataFrame):
    """Upload the DataFrame as prompts.csv to SharePoint."""
    token   = get_access_token()
    encoded = requests.utils.quote(f"{FOLDER_PATH}/{FILE_NAME}")
    upload_url = (
        f"{SHAREPOINT_URL}{SITE_PATH}/_api/web/"
        f"GetFolderByServerRelativeUrl('{SITE_PATH}{requests.utils.quote(FOLDER_PATH)}')"
        f"/Files/Add(url='{FILE_NAME}',overwrite=true)"
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "text/csv",
        "Accept":        "application/json;odata=verbose",
    }
    resp = requests.post(upload_url, data=csv_bytes, headers=headers)
    resp.raise_for_status()
