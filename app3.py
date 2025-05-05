import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from streamlit_option_menu import option_menu
from google.oauth2.service_account import Credentials
import gspread
# pip install google-api-python-client

# Configuración de la página
st.set_page_config(page_title="Mettatec Dashboard", page_icon=":bar_chart:", layout="wide")

# Autenticación con Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_info(
    st.secrets, scopes=SCOPES
)

service = build("sheets", "v4", credentials=credentials)

# ID de la hoja y nombre de la hoja
spreadsheet_id = "1n1RzG32GYqTAK8Zm_Iqg3PEdt9U_YG4Nx-YwRCopMm8"
sheet_name = "data"

@st.cache_data
def load_data():
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!B2:S101"  # Fila 2
    ).execute()

    values = result.get("values", [])

    if not values:
        st.warning("No se encontraron datos en la hoja de cálculo.")
        return pd.DataFrame()

    headers = values[0]
    data = values[1:]
    df = pd.DataFrame(data, columns=headers)
    return df

df = load_data()

# Mostrar tabla
st.title("Dashboard Trazabilidad Soporte")

# Sidebar - Menú principal
with st.sidebar:
    selected = option_menu(
        menu_title="Menú principal",
        options=["Consultas", "Estado del Equipo", "Reportes", "Etapas"],
        icons=["house", "gear", "activity", "layers"],
        menu_icon="cast",
        default_index=0
    )

# Sección de Consultas
if selected == "Consultas":
    st.header("Filtros de Consulta")

    cliente = st.multiselect("Seleccione el cliente:", options=df["NOMBRE / RAZÓN SOCIAL"].unique(), default=None)
    serial = st.multiselect("Seleccione el número de serie:", options=df["SERIAL"].unique(), default=None)

    df_filtered = df.copy()
    if cliente:
        df_filtered = df_filtered[df_filtered["NOMBRE / RAZÓN SOCIAL"].isin(cliente)]
    if serial:
        df_filtered = df_filtered[df_filtered["SERIAL"].isin(serial)]

    st.dataframe(df_filtered[["NOMBRE / RAZÓN SOCIAL", "MODELO", "SERIAL", "GARANTÍA", "ESTADO DE INGRESO"]])

# Sección de Reportes
if selected == "Reportes":
    st.header("Reportes")

    df["FECHA INGRESO"] = pd.to_datetime(df["FECHA INGRESO"],  errors='coerce', ) # date 
    df["AÑO"] = df["FECHA INGRESO"].dt.year
    df["MES"] = df["FECHA INGRESO"].dt.strftime('%d') ### to be corrected

    año_seleccionado = st.selectbox("Seleccione el año:", options=sorted(df["AÑO"].dropna().unique(), reverse=True))
    df_año = df[df["AÑO"] == año_seleccionado]

    df_grouped = df_año.groupby(["MES", "ACCIONES REALIZADAS"]).size().reset_index(name="CANTIDAD")

    fig_reportes = px.bar(
        df_grouped, x="MES", y="CANTIDAD", color="ACCIONES REALIZADAS",
        title=f"Cantidad de equipos solucionados en el {año_seleccionado} por mes",
        barmode='group'
    )
    st.plotly_chart(fig_reportes, use_container_width=True)

# Sección Estado del Equipo
if selected == "Estado del Equipo":
    st.header("Estado del Equipo")

    equipos_con_diagnostico = df[df["DIAGNÓSTICO INICIAL"].notna()]
    equipos_sin_diagnostico = df[df["DIAGNÓSTICO INICIAL"].isna()]

    st.write(f"**Cantidad de equipos con diagnóstico:** {len(equipos_con_diagnostico)}")
    st.write(f"**Cantidad de equipos sin diagnóstico:** {len(equipos_sin_diagnostico)}")

    fig_estado = px.bar(
        x=["Con diagnóstico", "Sin diagnóstico"],
        y=[len(equipos_con_diagnostico), len(equipos_sin_diagnostico)],
        title="Cantidad de equipos evaluados"
    )
    st.plotly_chart(fig_estado, use_container_width=True)
