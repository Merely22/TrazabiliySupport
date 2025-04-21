
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

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
