import streamlit as st
from streamlit_option_menu import option_menu
import sys
import os
import streamlit.components.v1 as components
from PIL import Image

sys.path.insert(0, os.getcwd())

st.set_page_config(
    page_title="Agro Analysis",
    layout="wide")

st.markdown("""
<style>
.big-font {
    font-size:80px !important;
}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    selected = option_menu('INTELIGÊNCIA AGRO', ['Visualizações','Sobre'],
                           icons=['play-btn','info-circle'], menu_icon="tree-fill", default_index=0,
                           styles={
                               "nav-link-selected": {"background-color": "#2c812c"}
                           })


if selected=="Visualizações":

    st.title('Monitoramento de Índices de Vegetação com Google Earth Engine')
    st.header('Visualização de Resultados')
    st.markdown(" Fazenda Batista - Situada no Interior de Minas Gerais")
    st.markdown(" Produção de Cana-de-Açúcar e Criação de Gado")
    st.divider()

    st.subheader('Visão Geral da Propriedade')
    with open("data/results/map.html", "r") as f:
        html_str = f.read()

    components.html(html_str, height=600)

    st.divider()

    st.subheader('Dados Temporais de NDVI')
    image = Image.open("data/results/temporal_ndvi_mean.png")
    st.image(image, caption='Tendência da Média de NDVI na Propriedade', use_column_width=True)

    st.divider()

    st.subheader('Gráfico de Linha NDVI')
    with open("data/results/iterative_ndvi.html", "r", encoding="utf-8") as f:
        html_str = f.read()
    components.html(html_str, height=400)

    st.divider()

    st.subheader('Timelapse NDVI')
    with open("data/results/images_slider.html", "r", encoding="utf-8") as f:
        html_str = f.read()
    components.html(html_str, height=500)

    st.divider()

    with st.container():
        col1,col2=st.columns(2)
        with col1:
            st.subheader('Histograma NDVI')
            with open("data/results/iterative_histogram.html", "r", encoding="utf-8") as f:
                html_str = f.read()

            components.html(html_str, height=400)
        with col2:
            st.subheader('BoxPlot NDVI por Ano')
            with open("data/results/iterative_boxplot.html", "r", encoding="utf-8") as f:
                html_str = f.read()
            components.html(html_str, height=400)

if selected=='Sobre':
    st.title('Dados')

    col1,col2,col3=st.columns(3)
    col1.subheader('Fonte')
    col2.subheader('Descrição')
    col3.subheader('Link')
    with st.container():
        col1,col2,col3=st.columns(3)

        col1.write(':blue[Ministério do Meio Ambiente e Mudança do Clima]')
        col2.write('Sicar - Sistema Nacional de Cadastro Ambiental Rural')
        col3.write('https://consultapublica.car.gov.br/publico/imoveis/index')

    with st.container():
        col1,col2,col3=st.columns(3)
        col1.write(':blue[Google Earth Engine]')
        col2.write('Earth Engine API')
        col3.write('https://earthengine.google.com/')


    st.divider()

    st.title('Criadora')
    with st.container():
        col1,col2=st.columns(2)
        col1.write('')
        col1.write('')
        col1.write('')
        col1.write('**Nome:**    Anne Carvalho')
        col1.write('**Educação:**    BS Ciência da Computação')
        col1.write('**Experiência:**    Ciência de Dados em Finanças e Seguros')
        col1.write('**Contato:**    anneisabelle.rodrigues@outlook.com ou [linkedin](https://www.linkedin.com/in/anne-isabelle-rodrigues-de-carvalho/)')
        col1.write('**Obrigada pela visita!**')

