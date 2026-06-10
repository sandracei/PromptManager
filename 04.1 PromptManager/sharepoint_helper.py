"""
sharepoint_helper.py — versión Azure App Service
Autenticación OAuth con cuenta de empresa via MSAL (authorization code flow).
"""

import os, io, json
import pandas as pd
import msal, requests
import streamlit as st

# ── Configuración — rellena estos valores ────────────────────────────────────
CLIENT_ID     = os.environ.get("AAD_CLIENT_ID", "TU_CLIENT_ID_AQUI")
CLIENT_SECRET = os.environ.get("AAD_CLIENT_SECRET", "TU_CLIENT_SECRET_AQUI")
TENANT_ID     = os.environ.get("AAD_TENANT_ID", "TU_TENANT_ID_AQUI")
REDIRECT_URI  = os.environ.get("REDIRECT_URI", "https://TUNOMBRE.azurewebsites.net/")

SHAREPOINT_URL = "https://corpdir.sharepoint.com"
SITE_PATH      = "/sites/DWT_OOEU"
FOLDER_PATH    = "/OOEU Workstream/Support Chatbot/Operational/04.1 PromptManager"
FILE_NAME      = "prompts.csv"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES    = ["https://corpdir.sharepoint.com/AllSites.ReadWrite", "User.Read"]

COLUMNS = ["id", "nombre", "descripcion", "prompt", "version",
           "cambios", "responsable", "fecha", "categoria", "activo", "precision", "test_file"]


# ── Auth helpers ─────────────────────────────────────────────────────────────
def _msal_app():
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )

def get_auth_url():
    """Generate the Microsoft login URL."""
    app = _msal_app()
    return app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state="streamlit",
    )

def exchange_code_for_token(code: str) -> dict:
    """Exchange the auth code (from redirect) for an access token."""
    app = _msal_app()
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return result

def get_access_token() -> str:
    """
    Returns a valid access token.
    If not logged in, shows a login button and stops rendering.
    """
    # Already have a token in session?
    token_data = st.session_state.get("token_data")

    if token_data and "access_token" in token_data:
        # Try silent refresh
        app = _msal_app()
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                st.session_state["token_data"] = result
                return result["access_token"]
        return token_data["access_token"]

    # Check for auth code in URL query params (after redirect)
    params = st.query_params
    if "code" in params:
        code = params["code"]
        result = exchange_code_for_token(code)
        if "access_token" in result:
            st.session_state["token_data"] = result
            st.query_params.clear()
            st.rerun()
        else:
            st.error(f"Error de autenticación: {result.get('error_description', result)}")
            st.stop()

    # Not logged in — show login screen
    auth_url = get_auth_url()
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
    min-height:60vh;gap:1.5rem;">
      <div style="font-size:3rem;">📚</div>
      <div style="font-size:1.5rem;font-weight:700;color:#1e293b;">Biblioteca de Prompts</div>
      <div style="color:#64748b;font-size:0.95rem;">Inicia sesión con tu cuenta de empresa para continuar</div>
    </div>
    """, unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        st.link_button(
            "🔐  Iniciar sesión con Microsoft",
            auth_url,
            use_container_width=True,
            type="primary",
        )
    st.stop()


# ── SharePoint read / write ──────────────────────────────────────────────────
def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json;odata=verbose",
    }

def load_from_sharepoint() -> pd.DataFrame:
    token    = get_access_token()
    encoded  = requests.utils.quote(f"{SITE_PATH}{FOLDER_PATH}/{FILE_NAME}")
    url      = f"{SHAREPOINT_URL}{SITE_PATH}/_api/web/GetFileByServerRelativeUrl('{encoded}')/$value"
    resp     = requests.get(url, headers=_headers(token))
    if resp.status_code == 404:
        return pd.DataFrame(columns=COLUMNS)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.content.decode("utf-8")))
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df

def save_to_sharepoint(df: pd.DataFrame):
    token        = get_access_token()
    folder_enc   = requests.utils.quote(f"{SITE_PATH}{FOLDER_PATH}")
    upload_url   = (
        f"{SHAREPOINT_URL}{SITE_PATH}/_api/web/"
        f"GetFolderByServerRelativeUrl('{folder_enc}')"
        f"/Files/Add(url='{FILE_NAME}',overwrite=true)"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "text/csv",
        "Accept":        "application/json;odata=verbose",
    }
    resp = requests.post(upload_url, data=df.to_csv(index=False).encode("utf-8"), headers=headers)
    resp.raise_for_status()


def upload_test_file(file_bytes: bytes, file_name: str) -> str:
    """
    Upload a test file to the Tests subfolder in SharePoint.
    Returns the stored file name (used as reference in the CSV).
    """
    token      = get_access_token()
    safe_name  = file_name.replace("'", "")          # avoid quote issues in REST URL
    folder_enc = requests.utils.quote(f"{SITE_PATH}{FOLDER_PATH}/Tests")

    # Make sure the Tests subfolder exists (ignore error if it already does)
    create_url = (
        f"{SHAREPOINT_URL}{SITE_PATH}/_api/web/"
        f"GetFolderByServerRelativeUrl('{requests.utils.quote(SITE_PATH + FOLDER_PATH)}')"
        f"/Folders/Add('Tests')"
    )
    requests.post(create_url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json;odata=verbose",
    })

    upload_url = (
        f"{SHAREPOINT_URL}{SITE_PATH}/_api/web/"
        f"GetFolderByServerRelativeUrl('{folder_enc}')"
        f"/Files/Add(url='{safe_name}',overwrite=true)"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/octet-stream",
        "Accept":        "application/json;odata=verbose",
    }
    resp = requests.post(upload_url, data=file_bytes, headers=headers)
    resp.raise_for_status()
    return safe_name


def download_test_file(file_name: str) -> bytes:
    """Download a test file from the Tests subfolder and return raw bytes."""
    token   = get_access_token()
    encoded = requests.utils.quote(f"{SITE_PATH}{FOLDER_PATH}/Tests/{file_name}")
    url     = f"{SHAREPOINT_URL}{SITE_PATH}/_api/web/GetFileByServerRelativeUrl('{encoded}')/$value"
    resp    = requests.get(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json;odata=verbose",
    })
    resp.raise_for_status()
    return resp.content
