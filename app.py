import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from streamlit_option_menu import option_menu
from google.oauth2.service_account import Credentials
import gspread
import plotly.graph_objects as go 
# pip install google-api-python-client
from datetime import datetime
from datetime import date 
from dateutil import parser
#========================================================================================
#========================================================================================
#========================================================================================

# Configuración de la página
st.set_page_config(page_title="Dashboard Trazabilidad", layout="wide")
st.title("Dashboard Trazabilidad Soporte")

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
        range=f"{sheet_name}!B2:AD101"  # modify by inserting more columns and rows 
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
#========================================================================================
#========================================================================================

# Sidebar - Menú principal
with st.sidebar:
    selected = option_menu(
        menu_title="Menú principal",
        options=["Inicio", "Consultas", "Estado del Equipo", "Reportes", "Etapas"],
        icons=["house", "search", "bar-chart","list-check", "clock"],
        menu_icon="cast",
        default_index=0
    )
#========================================================================================
# Sección de Inicio
if selected == "Inicio":
    st.header("Resumen General")
    
    # Tarjetas de resumen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Equipos", len(df))
    with col2:
        st.metric("Entregados", len(df[df["ENTREGADO CLIENTE"] == "SI"]))
    with col3:
        st.metric("Pendientes", len(df[df["ENTREGADO CLIENTE"] != "SI"]))
    
    # 1. Convertir la columna de fecha a datetime (si no lo está)
    df['FECHA INGRESO'] = pd.to_datetime(df['FECHA INGRESO'], format='%d/%m/%Y', errors='coerce')  # Ajusta el nombre de la columna
    df['MES'] = df['FECHA INGRESO'].dt.to_period('M').dt.strftime('%B') # Formato: YYYY-MM
    order = ['January', 'February', 'March', 'April', 'May', 'June', 
                'July', 'August', 'September', 'October', 'November', 'December']
    df['MES'] = pd.Categorical(df['MES'], categories=order, ordered=True)

    # 3. Contar equipos por mes
    equipos_por_mes = df['MES'].value_counts().sort_index()

    # 4. Gráfico con Streamlit (opción simple)
    st.subheader("Equipos ingresados por mes")
    st.bar_chart(equipos_por_mes,use_container_width=True)
#========================================================================================
# Sección de Consultas
elif selected == "Consultas":
    st.header("Filtros de Consulta")

    cliente = st.multiselect("Seleccione el cliente:", options=df["NOMBRE / RAZÓN SOCIAL"].unique(), default=None)
    serial = st.multiselect("Seleccione el número de serie:", options=df["SERIAL"].unique(), default=None)

    df_filtered = df.copy()
    if cliente:
        df_filtered = df_filtered[df_filtered["NOMBRE / RAZÓN SOCIAL"].isin(cliente)]
    if serial:
        df_filtered = df_filtered[df_filtered["SERIAL"].isin(serial)]

    st.dataframe(df_filtered[["NOMBRE / RAZÓN SOCIAL", "MODELO", "SERIAL", "GARANTÍA", "OBSERVACIONES CLIENTE"]])
#========================================================================================
# Sección de Reportes
elif selected == "Reportes":
    st.header("Reportes")

    df["FECHA INGRESO"] = pd.to_datetime(df["FECHA INGRESO"],  errors='coerce' ) # date 
    df["AÑO"] = df["FECHA INGRESO"].dt.year
    df["MES"] = pd.to_datetime(df["FECHA INGRESO"], errors='coerce').dt.strftime('%B') ## to be corrected

    año_seleccionado = st.selectbox("Seleccione el año:", options=sorted(df["AÑO"].dropna().unique(), reverse=True))
    df_año = df[df["AÑO"] == año_seleccionado]

    df_grouped = df_año.groupby(["MES", "ACCIONES REALIZADAS"]).size().reset_index(name="CANTIDAD")

    fig_reportes = px.bar(
        df_grouped, x="MES", y="CANTIDAD", color="ACCIONES REALIZADAS",
        title=f"Cantidad de equipos solucionados en el {año_seleccionado} por mes",
        barmode='group'
    )
    st.plotly_chart(fig_reportes, use_container_width=True)
#========================================================================================
# Sección Estado del Equipo
elif selected == "Estado del Equipo":
    st.header("Estado del Equipo")
    
    # Calcular valores

    equipos_con_diagnostico = df[df["ACCIONES REALIZADAS"].notna() & (df["ACCIONES REALIZADAS"] != "")]
    equipos_sin_diagnostico = df[df["ACCIONES REALIZADAS"].isna() | (df["ACCIONES REALIZADAS"] == "")]
    total_equipos = len(df)
    
    # Mostrar KPIs en columnas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Equipos con diagnóstico", 
                f"{len(equipos_con_diagnostico)}", 
                f"{len(equipos_con_diagnostico)/total_equipos*100:.1f}%")
    with col2:
        st.metric("Equipos pendientes", 
                f"{len(equipos_sin_diagnostico)}", 
                f"{len(equipos_sin_diagnostico)/total_equipos*100:.1f}%")
    
    # Crear gráfico de torta mejorado
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=['Con diagnóstico', 'Sin diagnóstico'],
        values=[len(equipos_con_diagnostico), len(equipos_sin_diagnostico)],
        hole=0.5,  # Donut style
        marker_colors=['#2ca02c', '#d62728'],  # Verde y rojo
        textinfo='percent+value',
        insidetextorientation='radial',
        hoverinfo='label+percent',
        textfont_size=16,
        pull=[0.1, 0]  # Efecto de separación
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar tabla detallada opcional
    with st.expander("Ver detalles por equipo"):
        st.dataframe(
            df[["NOMBRE / RAZÓN SOCIAL", "DIAGNÓSTICO INICIAL", "ACCIONES REALIZADAS"]],
            use_container_width=True,
            height=300
        )

#========================================================================================
# Seleccion stages
elif selected == "Etapas":
    st.header("Tiempos entre Etapas")
    df = df.copy()
    
    # Preprocesamiento de fechas y meses (corregido)
    df['FECHA INGRESO'] = pd.to_datetime(df['FECHA INGRESO'], format='%d/%m/%Y', errors='coerce')
    df['FECHA ENTREGA'] = pd.to_datetime(df['FECHA ENTREGA'], format='%d/%m/%Y', errors='coerce')
    df['MES'] = df['FECHA INGRESO'].dt.to_period('M').dt.strftime('%B')
    order = ['January', 'February', 'March', 'April', 'May', 'June', 
             'July', 'August', 'September', 'October', 'November', 'December']
    df['MES'] = pd.Categorical(df['MES'], categories=order, ordered=True)
    
    if not df.empty and all(col in df.columns for col in ["FECHA ENTREGA", "FECHA INGRESO"]):
        # Calcular tiempos
        df["Tiempo Total"] = (df["FECHA ENTREGA"] - df["FECHA INGRESO"]).dt.days
        
        # Mostrar KPIs mejorados
        cols = st.columns(4)  
        with cols[0]:
            avg_time = df["Tiempo Total"].mean()
            color = "green" if avg_time < 15 else "orange" if avg_time < 30 else "red"
            st.metric("Tiempo Promedio", 
                     f"{round(avg_time, 1)} días" if not pd.isna(avg_time) else "N/A",
                     delta_color="off",
                     help="Tiempo promedio de reparación",
                     label_visibility="visible")
        
        with cols[1]:
            min_time = df["Tiempo Total"].min()
            st.metric("Tiempo Mínimo", 
                     f"{min_time} días" if not pd.isna(min_time) else "N/A",
                     help="Tiempo más rápido de reparación")
        
        with cols[2]:
            max_time = df["Tiempo Total"].max()
            st.metric("Tiempo Máximo", 
                     f"{max_time} días" if not pd.isna(max_time) else "N/A",
                     help="Tiempo más lento de reparación")
        
        with cols[3]:
            median_time = df["Tiempo Total"].median()
            st.metric("Mediana", 
                     f"{median_time} días" if not pd.isna(median_time) else "N/A",
                     help="Punto medio de todos los tiempos")
        
        # Tabla detallada
        st.subheader("Detalle por Equipo")
        st.dataframe(df[["NOMBRE / RAZÓN SOCIAL", "FECHA INGRESO", "FECHA ENTREGA", "Tiempo Total"]],
                    use_container_width=True)
    else:
        st.warning("No hay datos suficientes para calcular tiempos")

