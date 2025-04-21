
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from google.oauth2.service_account import Credentials
import gspread

import sys
#st.write("Python executable in use:", sys.executable)
#st.write("sys.path:", sys.path)


# Configuración de la página
st.set_page_config(page_title="Mettatec Dashboard", page_icon=":bar_chart:", layout="wide")

# Cargar datos
@st.cache_data
def load_data(uploaded_file):
    return pd.read_excel(
        io=uploaded_file,
        engine='openpyxl',
        sheet_name='data',
        usecols='B:S',
        nrows=100,
        header=1, # La fila 2 en Excel
    )


st.title("Carga de archivo Excel")

# Widget para subir archivos de tipo Excel
uploaded_file = st.file_uploader("Selecciona un archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.write("Datos cargados:")
    st.dataframe(df)
else:
    st.info("Por favor, sube un archivo Excel para ver los datos.")

scope = [
    "https://www.googleapis.com/auth/spreadsheets", 
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("regal-muse-452714-a6-36c96a9e9e1e.json", scopes=scope)
client = gspread.authorize(creds)

try:
    # Listar todas las hojas de cálculo accesibles
    spreadsheets = client.openall()
    print("Hojas de cálculo disponibles:")
    for sheet in spreadsheets:
        print(" - " + sheet.title)
except Exception as e:
    print("Error al acceder a las hojas de cálculo:", e)


# Ejemplo para abrir una hoja de cálculo
#sheet = client.open("TRAZABILIDAD_SOPORTE").worksheet("data")
#data = sheet.get_all_records()

#print("DataFrame cargado:")
#print(df.columns.tolist())

# Sidebar - Menu principal 
with st.sidebar:
    selected = option_menu(
        menu_title="Menú principal",
        options=["Consultas", "Estado del Equipo", "Reportes", "Etapas"],
        icons=["house", "gear", "activity", "layers"],
        menu_icon="cast",
        default_index=0
    )

# Seccion de Consultas
if selected == "Consultas":
    with st.container():
        st.header("Filtros de Consulta")
        
        # Filtros
        cliente = st.multiselect("Seleccione el cliente:", options=df["NOMBRE / RAZÓN SOCIAL"].unique(), default=None)
        serial = st.multiselect("Seleccione el número de serie:", options=df["SERIAL"].unique(), default=None)
        
        df_filtered = df.copy()
        if cliente:
            df_filtered = df_filtered[df_filtered["NOMBRE / RAZÓN SOCIAL"].isin(cliente)]
        if serial:
            df_filtered = df_filtered[df_filtered["NOMBRE / RAZÓN SOCIAL"].isin(serial)]
        
        st.dataframe(df_filtered[["NOMBRE / RAZÓN SOCIAL", "MODELO", "SERIAL", "GARANTÍA", "ESTADO DE INGRESO"]])

# Sección de Reportes
if selected == "Reportes":
    with st.container():
        st.header("Reportes")
        
        # Extraer año y mes
        df["AÑO"] = pd.to_datetime(df["FECHA INGRESO"], errors='coerce').dt.year
        df["MES"] = pd.to_datetime(df["FECHA INGRESO"], errors='coerce').dt.strftime('%B')
        
        # Selección de año
        año_seleccionado = st.selectbox("Seleccione el año:", options=sorted(df["AÑO"].dropna().unique(), reverse=True))
        df_año = df[df["AÑO"] == año_seleccionado]

        print("DataFrame filtrado por año:")
        print(df_año.columns.tolist())
        
        # Agrupar por mes y responsable
        df_grouped = df_año.groupby(["MES", "ACCIONES REALIZADAS"]).size().reset_index(name="CANTIDAD")
        
        # Grafico equipos atendidos por soporte y/o tecnicos 
        fig_reportes = px.bar(
            df_grouped, x="MES", y="CANTIDAD", color="ACCIONES REALIZADAS",
            title=f"Cantidad de equipos solucionados en el {año_seleccionado} por mes",
            labels={"ACCIONES REALIZADAS": "Acciones realizadas"},
            #labels={"MES": "Mes", "CANTIDAD": "Cantidad de equipos"},
            barmode='group'
        )
        st.plotly_chart(fig_reportes, use_container_width=True)

# Sección de Estado del Equipo
if selected == "Estado del Equipo":
    with st.container():
        st.header("Estado del Equipo")
        
        equipos_con_diagnostico = df[df["DIAGNÓSTICO INICIAL"].notna()]
        equipos_sin_diagnostico = df[df["DIAGNÓSTICO INICIAL"].isna()]
        
        cantidad_con_diagnostico = len(equipos_con_diagnostico)
        cantidad_sin_diagnostico = len(equipos_sin_diagnostico)
        
        st.write(f"**Cantidad de equipos con diagnóstico:** {cantidad_con_diagnostico}")
        st.write(f"**Cantidad de equipos sin diagnóstico:** {cantidad_sin_diagnostico}")
        
        fig_estado = px.bar(
            x=["Equipos con diagnóstico", "Equipos sin diagnóstico"],
            y=[cantidad_con_diagnostico, cantidad_sin_diagnostico],
            title="Cantidad de equipos evaluados",
            labels={"x": "Categoría", "y": "Cantidad"}
        )
        st.plotly_chart(fig_estado, use_container_width=True)

