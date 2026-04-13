# interface.py
import streamlit as st
import ee
import geemap.foliumap as geemap

# IMPORTAÇÃO DA CLASSE SEPARADA
from motor import ConexaoEE

class AppInterface:
    """Gerencia a interface do usuário, layout e mapa com Streamlit."""
    
    def __init__(self):
        self.cidades = {
            "Rio Bonito do Iguaçu": [-52.529206, -25.487384]
        }
        self.vis_rgb = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000, 'gamma': 1.4}
        self.vis_ndvi = {'min': -1, 'max': 1, 'palette': ['blue', 'white', 'green']}
        self.vis_ndbi = {'min': -1, 'max': 1, 'palette': ['#ffffcc', '#a1dab4', '#41b6c4', '#2c7fb8', '#253494']}
        self.vis_ndwi = {'min': -1, 'max': 1, 'palette': ['white', 'blue']}

    def configurar_pagina(self):
        st.set_page_config(layout="wide", page_title="Análise de Cidades")
        st.title("Análise de Índices de Satélite por Cidade")
        st.markdown("Selecione uma cidade para calcular e visualizar os índices.")

    def criar_mapa_padrao(self):
        mapa = geemap.Map(center=[-30.0346, -51.2287], zoom=12)
        mapa.add_basemap("ROADMAP")
        mapa.add_basemap("HYBRID")
        return mapa

    def processar_cidade_no_mapa(self, cidade_nome, coords, col_painel):
        mapa = geemap.Map(location=[coords[1], coords[0]], zoom=12)
        mapa.add_basemap("HYBRID")

        aoi = ee.Geometry.Point(coords).buffer(10000).bounds()

        with col_painel:
            st.success(f"Processando todos os índices para {cidade_nome}...")

        with st.spinner("Buscando e processando imagens..."):
            try:
                # USANDO O BACK-END IMPORTADO
                colecao = ConexaoEE.obter_colecao_sentinel(aoi)
                
                if colecao.size().getInfo() == 0:
                    with col_painel:
                        st.warning("Nenhuma imagem recente com menos de 30% de nuvens encontrada.")
                    return mapa

                imagem_base = colecao.median()
                ndvi, ndbi, ndwi = ConexaoEE.calcular_indices(imagem_base)

                mapa.addLayer(imagem_base.clip(aoi), self.vis_rgb, f"RGB - {cidade_nome}")
                mapa.addLayer(ndvi.clip(aoi), self.vis_ndvi, f"NDVI - {cidade_nome}")
                mapa.addLayer(ndbi.clip(aoi), self.vis_ndbi, f"NDBI - {cidade_nome}")
                mapa.addLayer(ndwi.clip(aoi), self.vis_ndwi, f"NDWI - {cidade_nome}")

            except Exception as e:
                with col_painel:
                    st.error(f"Erro no Earth Engine: {e}")

        return mapa

    def executar(self):
        self.configurar_pagina()
        col_mapa, col_painel = st.columns([3, 1])

        with col_painel:
            st.subheader("Painel de Controle")
            cidade_selecionada = st.selectbox("Escolha a cidade", list(self.cidades.keys()))
            coords = self.cidades.get(cidade_selecionada)

        if not coords:
            mapa_final = self.criar_mapa_padrao()
        else:
            mapa_final = self.processar_cidade_no_mapa(cidade_selecionada, coords, col_painel)

        with col_mapa:
            mapa_final.to_streamlit(height=600)
            
