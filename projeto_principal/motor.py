import ee
import streamlit as st

class ConexaoEE:
    @staticmethod
    def autenticar(service_account, key_path):
        try:
            credentials = ee.ServiceAccountCredentials(service_account, key_path) # Autenticação API google earth engine
            ee.Initialize(credentials)
        except Exception as e:
            st.error(f"Erro ao inicializar: {e}")
            st.stop()

    @staticmethod
    def obter_imagem_rapida(aoi, data_inicial, data_final):
        """
        recebe as datas como parâmetros.
        Formato esperado: 'YYYY-MM-DD' (ex: '2023-01-01')
        """
        imagem = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi)
            .filterDate(data_inicial, data_final) # Usa as datas passadas pela interface
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .first()
        )
        return imagem

    @staticmethod
    def calcular_ndvi(imagem):
        return imagem.normalizedDifference(['B8', 'B4'])

    @staticmethod
    def calcular_mndwi(imagem):
        """
        Calcula o Modified Normalized Difference Water Index (MNDWI) para o Sentinel-2.
        Fórmula: (Verde - SWIR) / (Verde + SWIR) -> ['B3', 'B11']
        """
        return imagem.normalizedDifference(['B3', 'B11'])
