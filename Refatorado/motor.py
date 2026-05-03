import ee
import streamlit as st
from datetime import datetime, timedelta


class ConexaoEE:  # classe para conexão com google earth engine
    """Versão simplificada e rápida para testar a conexão e o mapa."""

    @staticmethod
    def autenticar(service_account, key_path):  # metodo para autenticação com o google earth engine
        try:  # tratamento de erros exception
            credentials = ee.ServiceAccountCredentials(service_account,
                                                       key_path)  # metodo do google para autenticar para usar o google earth engine
            ee.Initialize(credentials)
        except Exception as e:
            st.error(f"Erro ao inicializar: {e}")
            st.stop()

    @staticmethod
    def obter_imagem_rapida(aoi):  # metodo para obter a imagem
        # Pega os últimos 180 dias
        data_final = datetime.now()  # datetime.now() = metodo do python para pegar a hora do sistema
        data_inicial = data_final - timedelta(
            days=180)  # datetime usado para fazer a diferenciação de duas datas podia simplesmente colocar 180 dias

        # O SEGREDO DA VELOCIDADE: Usar .first() pega apenas 1 imagem pronta
        # em vez de processar uma pilha inteira de meses.
        imagem = (  # variavel imagem armazena os dados do processo abaixo
            ee.ImageCollection(
                'COPERNICUS/S2_SR_HARMONIZED')  # aqui  pega o catalogo de imagens do sentinell 2, SR significa que a imagem ja vem "formatada" do satelite removendo efeito de poeira e nevoa
            # armonized garatante que os dados de diferentes epocas de satelites sejam comparaveis entre si
            .filterBounds(aoi)  # aqui delimita a area de interesse
            .filterDate(data_inicial.strftime('%Y-%m-%d'),
                        data_final.strftime('%Y-%m-%d'))  # filtra as datas para 180 dias
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))  # mostra so imagens que tenham menos de 30% de nuvens
            .first()
        # aqui ele pega a primeira imagem mais limpa da lista para  e interrompe o processamento, se não fosse esse comando ele processsaria muito e daria varias imagens porem assim a primeira que vir ele interrompe e para
        )
        return imagem

    @staticmethod
    def calcular_ndvi(imagem):  # metodo para calcular nvdi
        # Calcula APENAS o NDVI para economizar memória
        return imagem.normalizedDifference(['B8', 'B4'])
