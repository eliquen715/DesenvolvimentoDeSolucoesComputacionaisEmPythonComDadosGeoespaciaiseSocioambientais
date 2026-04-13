# motor.py
import ee
import streamlit as st
from datetime import datetime, timedelta

class ConexaoEE:
    """Gerencia a autenticação e os cálculos no Google Earth Engine."""
    
    @staticmethod
    def autenticar(service_account, key_path):
        try:
            credentials = ee.ServiceAccountCredentials(service_account, key_path)
            ee.Initialize(credentials)
        except Exception as e:
            st.error(f"Erro ao inicializar com o Earth Engine: {e}")
            st.stop()

    @staticmethod
    def obter_colecao_sentinel(aoi, dias=240, max_nuvens=30):
        data_final = datetime.now()
        data_inicial = data_final - timedelta(days=dias)
        
        colecao = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi)
            .filterDate(data_inicial.strftime('%Y-%m-%d'), data_final.strftime('%Y-%m-%d'))
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', max_nuvens))
        )
        return colecao

    @staticmethod
    def calcular_indices(imagem_base):
        ndvi = imagem_base.normalizedDifference(['B8', 'B4'])
        ndbi = imagem_base.normalizedDifference(['B11', 'B8'])
        ndwi = imagem_base.normalizedDifference(['B3', 'B8'])
        return ndvi, ndbi, ndwi
