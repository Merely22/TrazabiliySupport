
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu


# Configuración de la página
st.set_page_config(page_title="Dashboard_Trazabilidad", page_icon=":bar_chart:", layout="wide")


# def load_data(uploaded_file):
#     return pd.read_excel(
#         io=uploaded_file,
#         engine='openpyxl',
#         sheet_name='data',
#         usecols='B:S',
#         nrows=100,
#         header=1, # La fila 2 en Excel
#     )


# st.title("Carga de archivo Excel")

# # Widget para subir archivos de tipo Excel
# uploaded_file = st.file_uploader("Selecciona un archivo Excel (.xlsx)", type=["xlsx"])

# if uploaded_file is not None:
#     df = load_data(uploaded_file)
#     st.write("Datos cargados:")
#     st.dataframe(df)
# else:
#     st.info("Por favor, sube un archivo Excel para ver los datos.")

scope = [
    "https://www.googleapis.com/auth/spreadsheets", 
    "https://www.googleapis.com/auth/drive"
]

# Carga las credenciales de la cuenta de servicio (ajusta la ruta al archivo JSON)
creds = Credentials.from_service_account_file("regal-muse-452714-a6-36c96a9e9e1e.json", scopes=scope)
client = gspread.authorize(creds)

# Define el nombre del documento de Google Sheets y la pestaña que deseas abrir
spreadsheet_name = "TRAZABILIDAD_SOPORTE"  
worksheet_name = "data"           

try:
    # Abrir la hoja de cálculo y seleccionar la pestaña deseada
    sheet = client.open(spreadsheet_name).worksheet(worksheet_name)
    
    # get_all_records() obtiene todos los registros usando la fila 2 como encabezado
    data = sheet.get_all_records(head=2)
    
    # Convertir la lista de diccionarios en un DataFrame de pandas
    df = pd.DataFrame(data)
        
    st.success("Hoja de cálculo cargada correctamente.")
    st.write("Datos de la hoja de cálculo:")
    st.dataframe(df)
    
except Exception as e:
    st.error("Error al acceder o leer la hoja de cálculo: " + str(e))


# lógica para procesar y visualizar los datos según tus necesidades


#============================================= Sidebar - Menu principal ====================================
# Sidebar - Menu principal
with st.sidebar:
    selected = option_menu(
        menu_title="Menú principal",
        options=["Consultas", "Estado del Equipo", "Reportes", "Etapas"],
        icons=["house", "gear", "activity", "layers"],
        menu_icon="cast",
        default_index=0
    )


#============================================= Consultas ====================================

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


#============================================= Reportes ====================================

if selected == "Reportes":
    with st.container():
        st.header("Reportes")

        df['FECHA INGRESO'] = pd.to_datetime(
        df['FECHA INGRESO'],
        dayfirst=True,     # indica formato DD/MM/YYYY
        errors='coerce'    # convierte valores inválidos a NaT
                                            )
        
        # Extraer año y mes
        df["AÑO"] = df["FECHA INGRESO"].dt.year
        df["MES"] = df['FECHA INGRESO'].dt.month_name()
        st.dataframe(df[["FECHA INGRESO", "AÑO", "MES"]])
        
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


#============================================= Estado del Equipo ===========================
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