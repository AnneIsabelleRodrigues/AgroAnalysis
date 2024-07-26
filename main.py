from gee_initialize import GoogleEarthEngine
import ee
import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geemap.foliumap as geemap

def apply_scl_mask(image):
    scl = image.select('SCL')
    vegetation_mask = scl.eq(4)
    return image.updateMask(vegetation_mask)

def calculate_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)

def get_ee_feature(geom):
    x,y = geom.exterior.coords.xy
    coords = np.dstack((x,y)).tolist()
    g = ee.Geometry.Polygon(coords)
    return ee.Feature(g)

def get_ee_geometry(geom):
    x,y = geom.exterior.coords.xy
    coords = np.dstack((x,y)).tolist()
    g = ee.Geometry.Polygon(coords)
    return g

def get_polygon():

    df = gpd.read_file(f'data/batista.shp')
    roi = df.iloc[0]['geometry']

    return roi

def df_ndvi():

    GoogleEarthEngine()

    roi = get_polygon()
    roi = get_ee_geometry(roi)

    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(roi)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .filterDate(ee.Date('2024-02-01'), ee.Date('2024-05-01')))

    collection_with_ndvi = collection.map(calculate_ndvi)

    collection_with_mask = collection_with_ndvi.map(apply_scl_mask)

    image_list = collection_with_mask.toList(collection_with_mask.size())

    all_data = []

    for i in range(collection_with_mask.size().getInfo()):
        image = ee.Image(image_list.get(i))

        mean_ndvi_region = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            scale=10,
            maxPixels=1e13
        )

        date = image.date().format("yyyy-MM-dd").getInfo()
        ndvi_mean = mean_ndvi_region.get('NDVI').getInfo()

        data = {'date': date, 'ndvi_mean': ndvi_mean}
        all_data.append(data)

    df = pd.DataFrame(all_data)
    df = df.drop_duplicates(subset='date', keep='last')

    return df


def display_timeseries():

    df = df_ndvi()
    df['date'] = pd.to_datetime(df['date'])
    df['date'] = df['date'].dt.strftime('%d/%m/%Y')

    plt.style.use('seaborn-v0_8-whitegrid')

    fig = plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['ndvi_mean'], marker='o', linestyle='-', color='g', markersize=8, linewidth=2, label='NDVI Mean')

    plt.title('Mean NDVI Over Time', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('NDVI Mean', fontsize=14)

    plt.ylim(-1, 1)

    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)

    plt.grid(True, linestyle='--', alpha=0.7)

    plt.legend()

    for i, row in df.iterrows():
        plt.text(row['date'], row['ndvi_mean'] + 0.04, f'{row["ndvi_mean"]:.2f}', ha='center', fontsize=10)

    plt.tight_layout()

    plt.savefig("temporal_ndvi_mean.png", format='png')

def mapdisplay():

    m = geemap.Map()

    m.add_basemap('SATELLITE')

    roi = get_polygon()

    # Cria um Feature collection do ee da lista
    features = ee.FeatureCollection([get_ee_feature(roi)])

    style = {
        'color': 'red',
        'width': 4,
        'fillColor': '00000000'
    }
    styled_polygon = features.style(**style)

    m.addLayer(styled_polygon, {}, 'Fazenda Batista')

    m.centerObject(features, zoom=15)
    m.to_html(filename='map.html')

def mapinterativo():

    m = geemap.Map()
    m.add_basemap('SATELLITE')

    roi = get_polygon()
    roi = get_ee_geometry(roi)

    geemap.modis_ndvi_timelapse(
        roi,
        out_gif='temporalndvi.gif',
        data='Terra',
        band='NDVI',
        start_date='2023-01-01',
        end_date='2024-12-31',
        frames_per_second=1,
        title='MODIS NDVI Timelapse'
    )

# if __name__ == '__main__':
#     display_timeseries()
#     mapdisplay()
#     mapinterativo()


