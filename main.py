from src.data_processing import DataProcessor
from src.data_visualization import NDVIVisualization

if __name__ == '__main__':

    DataProcessor = DataProcessor(shapefile_path='data/raw/batista.shp', start_date='2023-01-01')

    # Retorna o dataframe com os valores de NDVI e a feature usada para definir o local de análise
    df, feature = DataProcessor.get_all_data()

    # Salva imagens com filtro do NDVI direto do GEE
    DataProcessor.get_montly_images()

    NDVIVisualization = NDVIVisualization(df_data=df, start_date='2023-01-01', feature=feature)

    # Plota todos os mapas e gráficos utilizados para a visualização de dados
    NDVIVisualization.plot_ndvi_data()
    NDVIVisualization.plot_histograma_freq()
    NDVIVisualization.plot_mapdisplay()
    NDVIVisualization.plot_timeseries()
    NDVIVisualization.plot_boxplot()
    NDVIVisualization.plot_images_timelapse()
