import base64

import streamlit as st
from streamlit_option_menu import option_menu
import sys
import os
import streamlit.components.v1 as components
from PIL import Image

sys.path.insert(0, os.getcwd())

#Layout
st.set_page_config(
    page_title="Agro Analysis",
    layout="wide",
    initial_sidebar_state="expanded")

#Data Pull and Functions
st.markdown("""
<style>
.big-font {
    font-size:80px !important;
}
</style>
""", unsafe_allow_html=True)


#Options Menu
with st.sidebar:
    selected = option_menu('INTELIGÊNCIA AGRO', ['Visualizações','Sobre'],
                           icons=['play-btn','info-circle'], default_index=0,
                           styles={
                               "nav-link-selected": {"background-color": "#2c812c"},
                           })

#Intro Page

if selected=="Visualizações":
    #Header
    st.title('Monitoramento de Índices de Vegetação com Google Earth Engine')
    st.header('Visualização de Resultados')
    st.markdown("Batista - Fazenda no interior de Minas Gerais. Com plantações de Cana de Açúcar e criação de gado")
    st.divider()

    st.subheader('Visão Geral da Propriedade')
    with open("map.html", "r") as f:
        html_str = f.read()

    components.html(html_str, height=600)


    st.subheader('Dados Temporais de NDVI')
    image = Image.open("temporal_ndvi_mean.png")
    st.image(image, caption='Tendência da Média de NDVI na Propriedade', use_column_width=True)

    st.subheader('Timelapse NDVI (MODIS)')
    file_ = open("ndvi.gif", "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()

    st.markdown(
        f'<img src="data:image/gif;base64,{data_url}" alt="cat gif">',
        unsafe_allow_html=True,
    )

if selected=='Sobre':
    st.title('Dados')
    #st.subheader('All data for this project was publicly sourced from:')
    col1,col2,col3=st.columns(3)
    col1.subheader('Source')
    col2.subheader('Description')
    col3.subheader('Link')
    with st.container():
        col1,col2,col3=st.columns(3)
        #col1.image('census_graphic.png',width=150)
        col1.write(':blue[Ministério da Agricultura e Pecuária]')
        col2.write('Sistema de Subvenção Econômica ao Prêmio do Seguro Rural - SISSER')
        col3.write('https://dados.agricultura.gov.br/it/dataset/sisser3')

    with st.container():
        col1,col2,col3=st.columns(3)
        col1.write(':blue[Google Earth Engine]')
        col2.write('Earth Engine API')
        col3.write('https://earthengine.google.com/')


    st.divider()

    st.title('Creator')
    with st.container():
        col1,col2=st.columns(2)
        col1.write('')
        col1.write('')
        col1.write('')
        col1.write('**Nome:**    Anne Carvalho')
        col1.write('**Educação:**    BS Ciência da Computação')
        col1.write('**Experiência:**    Ciência de Dados em Finanças e Seguros')
        col1.write('**Contato:**    anneisabelle.rodrigues@outlook.com or [linkedin](https://www.linkedin.com/in/anne-isabelle-rodrigues-de-carvalho/)')
        col1.write('**Obrigada pela visita!**')

