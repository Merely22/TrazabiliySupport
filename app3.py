import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu

# Configuración de la página
st.set_page_config(page_title="Mettatec Dashboard", page_icon=":bar_chart:", layout="wide")

# Cargar datos
@st.cache_data
def load_data():
    return pd.read_excel(
        io='C:/Users/Merely/Downloads/projects/dashboard/Testing.xlsx',
        engine='openpyxl',
        sheet_name='data',
        usecols='B:R',
        nrows=100
    )

df = load_data()

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
        cliente = st.multiselect("Seleccione el cliente:", options=df["CLIENTE"].unique(), default=None)
        serial = st.multiselect("Seleccione el número de serie:", options=df["SERIAL"].unique(), default=None)
        
        df_filtered = df.copy()
        if cliente:
            df_filtered = df_filtered[df_filtered["CLIENTE"].isin(cliente)]
        if serial:
            df_filtered = df_filtered[df_filtered["SERIAL"].isin(serial)]
        
        st.dataframe(df_filtered[["CLIENTE", "MODELO", "SERIAL", "GARANTIA", "ESTADO_ACTUAL"]])

# Sección de Reportes
if selected == "Reportes":
    with st.container():
        st.header("Reportes")
        
        # Extraer año y mes
        df["AÑO"] = pd.to_datetime(df["FECHA_SOPORTE"], errors='coerce').dt.year
        df["MES"] = pd.to_datetime(df["FECHA_SOPORTE"], errors='coerce').dt.strftime('%B')
        
        # Selección de año
        año_seleccionado = st.selectbox("Seleccione el año:", options=sorted(df["AÑO"].dropna().unique(), reverse=True))
        df_año = df[df["AÑO"] == año_seleccionado]
        
        # Agrupar por mes y responsable
        df_grouped = df_año.groupby(["MES", "AREA_RESPONSABLE"]).size().reset_index(name="CANTIDAD")
        
        # Grafico equipos atendidos por soporte y/o tecnicos 
        fig_reportes = px.bar(
            df_grouped, x="MES", y="CANTIDAD", color="AREA_RESPONSABLE",
            title=f"Cantidad de equipos solucionados en el {año_seleccionado} por área responsable",
            labels={"MES": "Mes", "CANTIDAD": "Cantidad de equipos"},
            barmode='group'
        )
        st.plotly_chart(fig_reportes, use_container_width=True)

# Sección de Estado del Equipo
if selected == "Estado del Equipo":
    with st.container():
        st.header("Estado del Equipo")
        
        equipos_con_diagnostico = df[df["DIAGNOSTICO_INICIAL"].notna()]
        equipos_sin_diagnostico = df[df["DIAGNOSTICO_INICIAL"].isna()]
        
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

