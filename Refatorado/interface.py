import streamlit as st
import ee
import geemap.foliumap as geemap
from datetime import datetime, timedelta
from motor import ConexaoEE

COORDENADAS_RIO_BONITO = [-52.529206, -25.487384]

class AppInterface:
    def __init__(self):
        # Paletas do NDVI e Máscaras
        self.vis_agua = {'min': -1.0, 'max': -0.1, 'palette': ['#00008B', '#0000FF', '#00FFFF']}
        self.vis_solo = {'min': 0.0, 'max': 0.2, 'palette': ['#DEB887', '#8B4513']}
        self.vis_vegetacao = {'min': 0.2, 'max': 0.8, 'palette': ['#d9ef8b', '#a6d96a', '#1a9850', '#006837']}
        
        # --- NOVO: Parâmetros para ver a FOTO REAL (RGB) ---
        # As bandas B4 (Vermelho), B3 (Verde) e B2 (Azul) formam a visão do olho humano
        self.vis_rgb = {'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}

    def renderizar_aba(self, nome_aba, prefixo, data_referencia):
        col_mapa, col_painel = st.columns([3, 1])
        coords = COORDENADAS_RIO_BONITO

        data_fim_dt = datetime.strptime(data_referencia, '%Y-%m-%d')
        data_inicio_dt = data_fim_dt - timedelta(days=180)
        
        data_fim_str = data_fim_dt.strftime('%Y-%m-%d')
        data_inicio_str = data_inicio_dt.strftime('%Y-%m-%d')

        # --- PAINEL DE CONTROLE ---
        with col_painel:
            st.write(f"### Filtros - {nome_aba}")
            
            # Novo botão no painel para a Foto Real
            exibir_rgb = st.checkbox("🌍 Visualizar Foto Real (RGB)", value=True, key=f"rgb_{prefixo}")
            
            exibir_agua = st.checkbox("💧 Visualizar Água", value=False, key=f"agua_{prefixo}")
            exibir_solo = st.checkbox("🟤 Visualizar Solo", value=False, key=f"solo_{prefixo}")
            exibir_veg = st.checkbox("🌳 Visualizar NDVI", value=False, key=f"veg_{prefixo}")
            
            st.info(
                f"**Data base:** {data_fim_dt.strftime('%d/%m/%Y')}\n\n"
                f"**Período de busca (30 dias):**\n"
                f"{data_inicio_dt.strftime('%d/%m/%Y')} até {data_fim_dt.strftime('%d/%m/%Y')}"
            )

        # --- CONSTRUÇÃO DO MAPA ---
        with col_mapa:
            mapa = geemap.Map(location=[coords[1], coords[0]], zoom=15)
            mapa.add_basemap("HYBRID") # Mantém o fundo do Google Maps
            
            aoi = ee.Geometry.Point(coords).buffer(10000).bounds()

            with st.spinner(f"Buscando imagens limpas de {data_inicio_str} a {data_fim_str}..."):
                try:
                    imagem_base = ConexaoEE.obter_imagem_rapida(aoi, data_inicio_str, data_fim_str)
                    ndvi = ConexaoEE.calcular_ndvi(imagem_base)

                    # --- ADICIONA A FOTO REAL AO MAPA ---
                    # Esta linha garante que a imagem vá para o menu no canto superior direito!
                    if exibir_rgb:
                        mapa.addLayer(imagem_base.clip(aoi), self.vis_rgb, "Foto Real do Satélite")

                    # As camadas antigas
                    if exibir_agua:
                        agua_mask = ndvi.updateMask(ndvi.lt(0))
                        mapa.addLayer(agua_mask.clip(aoi), self.vis_agua, "Recursos Hídricos")

                    if exibir_solo:
                        solo_mask = ndvi.updateMask(ndvi.gte(0).And(ndvi.lt(0.2)))
                        mapa.addLayer(solo_mask.clip(aoi), self.vis_solo, "Solo Exposto")

                    if exibir_veg:
                        veg_mask = ndvi.updateMask(ndvi.gte(0.2))
                        mapa.addLayer(veg_mask.clip(aoi), self.vis_vegetacao, "Vegetação Saudável")

                except Exception as e:
                    st.error(f"Erro ao carregar a imagem: {e}")

            mapa.to_streamlit(height=600, key=f"map_display_{prefixo}")

    def executar(self):
        st.set_page_config(layout="wide", page_title="Monitoramento Temporal")
        st.title("COMPARAÇÃO DE PERÍODOS DE TEMPO")

        aba1, aba2 = st.tabs(["📍 Outubro 2025", "📍 Março 2026"])

        with aba1:
            self.renderizar_aba("Outubro 2025", "aba_out", "2025-10-01")

        with aba2:
            self.renderizar_aba("Março 2026", "aba_mar", "2026-03-15")
