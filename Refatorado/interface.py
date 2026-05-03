import streamlit as st
import ee
import geemap.foliumap as geemap
from motor import ConexaoEE

COORDENADAS_RIO_BONITO = [-52.529206, -25.487384]

class AppInterface:
    def __init__(self):
        # Configuramos as paletas específicas para cada tipo de alvo
        self.vis_agua = {'min': -1.0, 'max': -0.1, 'palette': ['#00008B', '#0000FF', '#00FFFF']}
        self.vis_solo = {'min': 0.0, 'max': 0.2, 'palette': ['#DEB887', '#8B4513']}
        self.vis_vegetacao = {'min': 0.2, 'max': 0.8, 'palette': ['#d9ef8b', '#a6d96a', '#1a9850', '#006837']}

    def executar(self):
        st.set_page_config(layout="wide", page_title="Monitoramento Socioambiental")
        st.title("PROJETO DE EXTENSÃO UNIVERSITÁRIA - NÚCLEOS DE COOPERAÇÃO")

        col_mapa, col_painel = st.columns([3, 1])
        coords = COORDENADAS_RIO_BONITO

        # --- PAINEL DE CONTROLE (AS CAIXAS DE SELEÇÃO) ---
        with col_painel:
            st.write("### Filtros de Camada")
            exibir_agua = st.checkbox("💧 Visualizar Água (Profunda/Rasa)", value=True)
            exibir_solo = st.checkbox("🟤 Visualizar Solo Exposto", value=False)
            exibir_veg = st.checkbox("🌳 Visualizar Vegetação (NDVI)", value=True)
            
            st.info("As camadas selecionadas serão sobrepostas no mapa.")

        # --- CONSTRUÇÃO DO MAPA ---
        with col_mapa:
            mapa = geemap.Map(location=[coords[1], coords[0]], zoom=15)
            mapa.add_basemap("HYBRID")
            
            aoi = ee.Geometry.Point(coords).buffer(10000).bounds()

            with st.spinner("Processando dados de satélite..."):
                try:
                    imagem_base = ConexaoEE.obter_imagem_rapida(aoi)
                    ndvi = ConexaoEE.calcular_ndvi(imagem_base)

                    # LÓGICA DE SOBREPOSIÇÃO:
                    # Só adiciona a camada se a caixa correspondente estiver marcada
                    
                    if exibir_agua:
                        # Mascaramos para mostrar apenas valores negativos (água)
                        agua_mask = ndvi.updateMask(ndvi.lt(0))
                        mapa.addLayer(agua_mask.clip(aoi), self.vis_agua, "Recursos Hídricos")

                    if exibir_solo:
                        # Mascaramos para mostrar apenas solo (entre 0 e 0.2)
                        solo_mask = ndvi.updateMask(ndvi.gte(0).And(ndvi.lt(0.2)))
                        mapa.addLayer(solo_mask.clip(aoi), self.vis_solo, "Solo Exposto")

                    if exibir_veg:
                        # Mascaramos para mostrar apenas vegetação (acima de 0.2)
                        veg_mask = ndvi.updateMask(ndvi.gte(0.2))
                        mapa.addLayer(veg_mask.clip(aoi), self.vis_vegetacao, "Vegetação Saudável")

                    st.success("Mapa renderizado!")

                except Exception as e:
                    st.error(f"Erro ao carregar dados: {e}")

            mapa.to_streamlit(height=600)
