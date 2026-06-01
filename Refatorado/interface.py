import streamlit as st
import ee
import geemap.foliumap as geemap
from datetime import datetime, timedelta
import locale
import streamlit.components.v1 as components  # <--- Importante para a injeção do PWA

# Importa o seu módulo local (certifique-se de que o motor.py possui a atualização do calcular_bci)
from motor import ConexaoEE

COORDENADAS_RIO_BONITO = [-52.529206, -25.487384]

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf-8')
except locale.Error:
    pass 

def injetar_pwa():
    """Injeta as tags de manifesto e registra o service worker do PWA na janela principal"""
    pwa_script = """
    <script>
        const parentDoc = window.parent.document;
        
        // Evita injetar o manifesto múltiplas vezes caso a página recarregue
        if (!parentDoc.querySelector('link[rel="manifest"]')) {
            const manifest = parentDoc.createElement('link');
            manifest.rel = 'manifest';
            manifest.href = '/app/static/manifest.json';
            parentDoc.head.appendChild(manifest);
        }

        // Registra o Service Worker na janela principal
        if ('serviceWorker' in window.parent.navigator) {
            window.parent.navigator.serviceWorker.register('/app/static/sw.js')
                .then(reg => console.log('Service Worker registrado com sucesso!', reg))
                .catch(err => console.error('Erro ao registrar Service Worker:', err));
        }
    </script>
    """
    # Altura e largura 0 para o iframe invisível na renderização do Streamlit
    components.html(pwa_script, height=0, width=0)

class AppInterface:
    def __init__(self):
        # Paletas do NDVI, MNDWI, BCI e Máscaras
        self.vis_agua = {'min': 0.0, 'max': 0.5, 'palette': ['#00FFFF', '#0000FF', '#00008B']} 
        self.vis_solo = {'min': 0.0, 'max': 0.2, 'palette': ['#DEB887', '#8B4513']}
        self.vis_vegetacao = {'min': 0.2, 'max': 0.8, 'palette': ['#d9ef8b', '#a6d96a', '#1a9850', '#006837']}
        self.vis_rgb = {'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}
        
        # Variáveis de data iniciais (Padrão ao abrir o app)
        self.dataInicial = datetime(2025, 5, 30).date()
        self.dataFinal = datetime(2026, 3, 13).date()

    def renderizar_aba(self, nome_aba, prefixo, data_selecionada):
        col_mapa, col_painel = st.columns([3, 1])
        coords = COORDENADAS_RIO_BONITO

        # A data_selecionada já vem como objeto "date" direto do executar()
        data_fim_dt = data_selecionada
        data_inicio_dt = data_fim_dt - timedelta(days=30) 
        
        # Converte para string para enviar ao Earth Engine
        data_fim_str = data_fim_dt.strftime('%Y-%m-%d')
        data_inicio_str = data_inicio_dt.strftime('%Y-%m-%d')

        # --- PAINEL DE CONTROLE ---
        with col_painel:
            st.write("### Filtros do Mapa")
            
            exibir_rgb = st.checkbox("🌍 Visualizar Foto Real (RGB)", value=False, key=f"rgb_{prefixo}")
            exibir_agua = st.checkbox("💧 Visualizar Água (MNDWI)", value=False, key=f"agua_{prefixo}")
            exibir_solo = st.checkbox("🟤 Visualizar Solo", value=False, key=f"solo_{prefixo}")
            exibir_veg = st.checkbox("🌳 Visualizar NDVI", value=False, key=f"veg_{prefixo}")
            
            st.info(
                f"**Data base:** {data_fim_dt.strftime('%d/%m/%Y')}\n\n"
                f"**Período de busca (180 dias):**\n"
                f"{data_inicio_dt.strftime('%d/%m/%Y')} até {data_fim_dt.strftime('%d/%m/%Y')}"
            )

        # --- CONSTRUÇÃO DO MAPA ---
        with col_mapa:
            mapa = geemap.Map(location=[coords[1], coords[0]], zoom=15)
            mapa.add_basemap("HYBRID") 
            
            aoi = ee.Geometry.Point(coords).buffer(10000).bounds()

            with st.spinner(f"Buscando imagens de {data_inicio_str} a {data_fim_str}..."):
                try:
                    imagem_base = ConexaoEE.obter_imagem_rapida(aoi, data_inicio_str, data_fim_str)
                    
                    # Cálculos dos Índices
                    ndvi = ConexaoEE.calcular_ndvi(imagem_base)
                    mndwi = ConexaoEE.calcular_mndwi(imagem_base)

                    if exibir_rgb:
                        mapa.addLayer(imagem_base.clip(aoi), self.vis_rgb, "Foto Real do Satélite")

                    if exibir_agua:
                        # Usando MNDWI > 0 para isolar a água
                        agua_mask = mndwi.updateMask(mndwi.gt(0))
                        mapa.addLayer(agua_mask.clip(aoi), self.vis_agua, "Recursos Hídricos (MNDWI)")

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
        
        # --- ATIVAÇÃO DO PWA ---
        injetar_pwa()  # <--- Injeta dinamicamente as configurações do PWA no navegador
        
        st.title("COMPARAÇÃO DE PERÍODOS DE TEMPO")

        # --- SELEÇÃO DE DATAS GLOBAL ---
        st.write("#### Selecione as datas base para comparação:")
        col1, col2 = st.columns(2)
        
        with col1:
            nova_data_inicial = st.date_input(
                "📅 Data para a Aba 1",
                value=self.dataInicial,format="DD/MM/YYYY",
                key="calendario_aba1"
            )
            
        with col2:
            nova_data_final = st.date_input(
                "📅 Data para a Aba 2",
                value=self.dataFinal,format="DD/MM/YYYY",
                key="calendario_aba2"
            )

        # Atualiza os atributos da classe com as novas escolhas
        self.dataInicial = nova_data_inicial
        self.dataFinal = nova_data_final

        # Cria os títulos dinamicamente baseados na escolha do usuário
        titulo_aba1 = f"📍 {self.dataInicial.strftime('%d/%m/%Y')}"
        titulo_aba2 = f"📍 {self.dataFinal.strftime('%d/%m/%Y')}"

        # Cria as abas com os novos títulos
        aba1, aba2 = st.tabs([titulo_aba1, titulo_aba2])

        # Envia a data como parâmetro (objeto date)
        with aba1:
            self.renderizar_aba(titulo_aba1, "aba_out", self.dataInicial)

        with aba2:
            self.renderizar_aba(titulo_aba2, "aba_mar", self.dataFinal)
