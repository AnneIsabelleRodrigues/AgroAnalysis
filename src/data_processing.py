from datetime import datetime
import ee
import geopandas as gpd
import numpy as np
import base64
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from dateutil.relativedelta import relativedelta

class DataProcessor:
    def __init__(self, shapefile_path, start_date, cloud_coverage_threshold=20):

        ee.Initialize(project='merxproject-430516')

        self.shapefile_path = shapefile_path
        self.start_date_str = start_date
        self.start_date = datetime.strptime(self.start_date_str, '%Y-%m-%d')
        self.end_date = self.start_date + relativedelta(years=1)
        self.cloud_coverage_threshold = cloud_coverage_threshold
        self.roi = self.get_polygon()
        self.roi_ee = self.get_ee_geometry(self.roi)
        self.ee_feature = self.get_ee_feature(self.roi_ee)

    @staticmethod
    def get_ee_geometry(geom):
        """Converte as coordenadas da geometria no Poligono do Earth Engine."""
        x, y = geom.exterior.coords.xy
        coords = np.dstack((x, y)).tolist()
        return ee.Geometry.Polygon(coords)

    @staticmethod
    def get_ee_feature(roi_ee):
        """Converte a Geometria em Earth Engine Feature."""
        return ee.Feature(roi_ee)

    @staticmethod
    def encode_image(image_path):
        """Encoda uma imagem para base64"""
        with open(image_path, 'rb') as f:
            image = f.read()
        return base64.b64encode(image).decode()

    @staticmethod
    def calculate_ndvi(image):
        """Realiza o cáclulo do NDVI sobre uma imagem"""

        nir = image.select('B8')
        red = image.select('B4')
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')

        #ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)

    def get_polygon(self):
        """Lê um shapefile e retorna a geometria da primeira e única propriedade"""
        df = gpd.read_file(self.shapefile_path)
        return df.iloc[0]['geometry']

    def get_image_collection(self, s_date, e_date):
        """Recupera uma coleção de imagens pelo GEE e mapeia cada imagem da coleção para o cálculo NDVI"""
        collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                      .filterBounds(self.roi_ee)
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self.cloud_coverage_threshold))
                      .filterDate(s_date, e_date))

        collection_with_ndvi = collection.map(self.calculate_ndvi)

        return collection_with_ndvi

    def get_all_data(self):
        """Resgata os dados de NDVI para uma região de interesse, salva em arquivo CSV e retorna os dados."""

        collection_with_ndvi = self.get_image_collection(self.start_date_str, self.end_date)

        image_list = collection_with_ndvi.toList(collection_with_ndvi.size())

        all_data = []

        combined_reducer = (ee.Reducer.mean()
                            .combine(reducer2=ee.Reducer.min(), sharedInputs=True)
                            .combine(reducer2=ee.Reducer.max(), sharedInputs=True)
                            .combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)
                            .combine(reducer2=ee.Reducer.median(), sharedInputs=True))

        for i in range(image_list.size().getInfo()):
            image = ee.Image(image_list.get(i))

            ndvi_region = image.reduceRegion(
                reducer=combined_reducer,
                geometry=self.roi_ee,
                scale=10,
                maxPixels=1e13
            )

            date = image.date().format("yyyy-MM-dd").getInfo()

            data = {
                'date': date,
                'ndvi_mean': ndvi_region.get('NDVI_mean').getInfo(),
                'ndvi_max': ndvi_region.get('NDVI_max').getInfo(),
                'ndvi_min': ndvi_region.get('NDVI_min').getInfo(),
                'ndvi_median': ndvi_region.get('NDVI_median').getInfo(),
                'ndvi_stdDev': ndvi_region.get('NDVI_stdDev').getInfo(),
            }
            all_data.append(data)

        df = pd.DataFrame(all_data).drop_duplicates(subset='date', keep='last')
        df.to_csv('data/processed/ndvi.csv', index=False)

        return df, self.ee_feature

    def get_montly_images(self) -> None:
        """Faz download do terreno em png como um heatmap em relação ao valor da mediana NDVI"""
        dates_months = list(pd.date_range(start=self.start_date, periods=12, freq='1M'))

        for date in dates_months:
            s_date = date.replace(day=1).strftime('%Y-%m-%d')
            e_date = date.strftime('%Y-%m-%d')
            save_date = date.strftime('%Y%m')

            collection_with_ndvi = self.get_image_collection(s_date, e_date)

            image = collection_with_ndvi.select('NDVI')

            mediana = image.median().clip(self.roi_ee)

            download_url = mediana.getThumbURL({
                'region': self.roi_ee,
                'dimensions': '512x512',
                'min': -1,
                'max': 1,
                'bands': ['NDVI'],
                'palette': [
                    'ffffff', 'ce7e45', 'df923d', 'f1b555', 'fcd163', '99b718', '74a901',
                    '66a000', '529400', '3e8601', '207401', '056201', '004c00', '023b01',
                    '012e01', '011d01', '011301'
                ],

                'format': 'png'})

            response = requests.get(download_url)
            imagem = Image.open(BytesIO(response.content))

            imagem.save(f'data/results/ndvi_{save_date}.png', 'PNG')


processor = DataProcessor('data/raw/batista.shp', '2023-01-01', '2023-12-30')
