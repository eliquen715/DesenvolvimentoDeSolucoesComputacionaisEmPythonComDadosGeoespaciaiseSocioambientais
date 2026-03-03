import streamlit as st
import geemap.foliumap as geemap
import ee

# Inicializa o Earth Engine
ee.Initialize(project='rs-pos-chuva')

st.title("Visualização NDVI e NDBI - Sentinel-2")

# ===========================
# CONFIGURAÇÕES
# ===========================
aoi = ee.Geometry.Polygon([
    [[-51.25, -30.0],
     [-51.25, -30.2],
     [-51.0,  -30.2],
     [-51.0,  -30.0]]
])

data_inicio = '2023-01-01'
data_fim    = '2023-03-31'

# ===========================
# COLEÇÃO SENTINEL-2 L2A
# ===========================
colecao = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterBounds(aoi)
           .filterDate(data_inicio, data_fim)
           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
           .median()
           .clip(aoi))

# ===========================
# CÁLCULO DO NDVI E NDBI
# ===========================
nir  = colecao.select('B8')
red  = colecao.select('B4')
swir = colecao.select('B11')

ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
ndbi = swir.subtract(nir).divide(swir.add(nir)).rename('NDBI')

# ===========================
# VISUALIZAÇÃO NO STREAMLIT
# ===========================
Map = geemap.Map(center=[-30.1, -51.1], zoom=12)
Map.addLayer(colecao.select(['B4','B3','B2']), {'min':0,'max':3000}, 'Sentinel-2 RGB')
Map.addLayer(ndvi, {'min':-1,'max':1,'palette':['white','green']}, 'NDVI')
Map.addLayer(ndbi, {'min':-1,'max':1,'palette':['white','brown']}, 'NDBI')
Map.addLayer(aoi, {'color': 'yellow'}, 'AOI')

# Renderiza no Streamlit
Map.to_streamlit(height=600)
