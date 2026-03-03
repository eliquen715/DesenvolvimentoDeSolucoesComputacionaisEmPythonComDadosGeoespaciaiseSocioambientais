import streamlit as st
import ee
import geemap.foliumap as geemap
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Análise de Cidades (RS)")

# --- AUTENTICAÇÃO E INICIALIZAÇÃO DO EARTH ENGINE ---
try:
    service_account = 'rs-pos-deploy@rs-pos-chuva.iam.gserviceaccount.com'
    key_path = '.private-key.json'
    credentials = ee.ServiceAccountCredentials(service_account, key_path)
    ee.Initialize(credentials)
except Exception as e:
    st.error(f"Erro ao inicializar ou autenticar com o Earth Engine: {e}")
    st.info("Verifique se o caminho para o arquivo de chave (.private-key.json) está correto e se a conta de serviço tem as permissões necessárias.")
    st.stop()

# --- DADOS DAS CIDADES ---
CIDADES_POA = {
    "Selecione uma cidade...": None,
    "Porto Alegre (Centro)": [-51.2287, -30.0346],
    "Canoas": [-51.1823, -29.9198],
    "Gravataí": [-50.9934, -29.9431],
    "Novo Hamburgo": [-51.1311, -29.6881],
    "São Leopoldo": [-51.1477, -29.7618],
    "Viamão": [-51.0235, -30.0811]
}

# --- TÍTULO E DESCRIÇÃO ---
st.title("Análise de Índices de Satélite por Cidade")
st.markdown("Selecione uma cidade para calcular e visualizar os índices NDVI (Vegetação), NDBI (Área Construída), NDWI (Água) e a imagem de Cor Real (RGB).")

# --- LAYOUT ---
col1, col2 = st.columns([3, 1])

# --- PAINEL DE CONTROLE (COLUNA 2) ---
with col2:
    st.subheader("Painel de Controle")
    cidade_selecionada_nome = st.selectbox(
        label="Escolha a cidade para analisar",
        options=list(CIDADES_POA.keys())
    )
    coords = CIDADES_POA.get(cidade_selecionada_nome)

# --- LÓGICA PRINCIPAL E CRIAÇÃO DO MAPA ---
# A criação do mapa agora depende da seleção do usuário em cada execução do script

if not coords:
    # Se nenhuma cidade foi selecionada, cria um mapa de visão geral
    Map = geemap.Map(center=[-30.0346, -51.2287], zoom=12)
    Map.add_basemap("ROADMAP")
    Map.add_basemap("SATELLITE")
    Map.add_basemap("HYBRID")
    with col2:
        st.info("Aguardando a seleção de uma cidade.")
else:
    # Se uma cidade foi selecionada, cria um mapa já focado e com zoom
    Map = geemap.Map(location=[coords[1], coords[0]], zoom=12)
    Map.add_basemap("HYBRID") # Inicia com híbrido para melhor contexto
    Map.add_basemap("SATELLITE")
    Map.add_basemap("ROADMAP")

    # Define a Área de Interesse (AOI)
    aoi = ee.Geometry.Point(coords).buffer(10000).bounds()

    with col2:
        st.success(f"Processando todos os índices para {cidade_selecionada_nome}...")

    with st.spinner("Buscando e processando imagens..."):
        try:
            # Período de busca dinâmico
            data_final = datetime.now()
            data_inicial = data_final - timedelta(days=240)
            data_inicial_str = data_inicial.strftime('%Y-%m-%d')
            data_final_str = data_final.strftime('%Y-%m-%d')
            
            # Coleta da coleção de imagens
            colecao_sentinel = (
                ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(aoi)
                .filterDate(data_inicial_str, data_final_str)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            )

            tamanho_colecao = colecao_sentinel.size().getInfo()

            if tamanho_colecao == 0:
                with col2:
                    st.warning(f"Nenhuma imagem com menos de 30% de nuvens foi encontrada nos últimos 8 meses para esta área.")
            else:
                imagem_sentinel_base = colecao_sentinel.median()

                # Adiciona as camadas ao mapa recém-criado
                vis_rgb = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000, 'gamma': 1.4}
                Map.addLayer(imagem_sentinel_base.clip(aoi), vis_rgb, f"RGB - {cidade_selecionada_nome}")

                ndvi = imagem_sentinel_base.normalizedDifference(['B8', 'B4'])
                vis_ndvi = {'min': -1, 'max': 1, 'palette': ['blue', 'white', 'green']}
                Map.addLayer(ndvi.clip(aoi), vis_ndvi, f"NDVI - {cidade_selecionada_nome}")

                ndbi = imagem_sentinel_base.normalizedDifference(['B11', 'B8'])
                vis_ndbi = {'min': -1, 'max': 1, 'palette': ['#ffffcc', '#a1dab4', '#41b6c4', '#2c7fb8', '#253494']}
                Map.addLayer(ndbi.clip(aoi), vis_ndbi, f"NDBI - {cidade_selecionada_nome}")
                
                ndwi = imagem_sentinel_base.normalizedDifference(['B3', 'B8'])
                vis_ndwi = {'min': -1, 'max': 1, 'palette': ['white', 'blue']}
                Map.addLayer(ndwi.clip(aoi), vis_ndwi, f"NDWI - {cidade_selecionada_nome}")

                with col2:
                    st.success("Análises concluídas! Use o controle de camadas no mapa para explorar.")

        except Exception as e:
            with col2:
                st.error(f"Ocorreu um erro durante o processamento no Earth Engine: {e}")

# --- RENDERIZAÇÃO FINAL DO MAPA (COLUNA 1) ---
# O mapa é renderizado aqui, depois de ter sido totalmente configurado
with col1:
    Map.to_streamlit(height=600)