import base64
from gee_initialize import GoogleEarthEngine
import ee
import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geemap.foliumap as geemap
import plotly.graph_objs as go
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO

plt.style.use('seaborn-v0_8-whitegrid')

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
                  .filterDate(ee.Date('2023-01-01'), ee.Date('2023-12-30')))

    collection_with_ndvi = collection.map(calculate_ndvi)

    image_list = collection_with_ndvi.toList(collection_with_ndvi.size())

    all_data = []

    for i in range(collection_with_ndvi.size().getInfo()):
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

    fig = plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['ndvi_mean'], marker='o', linestyle='-', color='g', markersize=8, linewidth=2, label='NDVI Médio')

    plt.title('Evolução da Média de NDVI', fontsize=16, fontweight='bold')
    plt.xlabel('Data', fontsize=14)
    plt.ylabel('NDVI Médio', fontsize=14)

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


def df_ndvi_all():

    GoogleEarthEngine()

    roi = get_polygon()
    roi = get_ee_geometry(roi)

    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(roi)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .filterDate(ee.Date('2023-01-01'), ee.Date('2023-12-30')))

    collection_with_ndvi = collection.map(calculate_ndvi)

    collection_with_mask = collection_with_ndvi.map(apply_scl_mask)

    image_list = collection_with_mask.toList(collection_with_mask.size())

    all_data = []

    combined_reducer = (ee.Reducer.mean()
                        .combine(reducer2=ee.Reducer.min(), sharedInputs=True)
                        .combine(reducer2=ee.Reducer.max(), sharedInputs=True)
                        .combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)
                        .combine(reducer2=ee.Reducer.median(), sharedInputs=True)
                        .combine(reducer2=ee.Reducer.percentile([25, 50, 75]), sharedInputs=True))

    for i in range(collection_with_mask.size().getInfo()):
        image = ee.Image(image_list.get(i))

        ndvi_region = image.reduceRegion(
            reducer=combined_reducer,
            geometry=roi,
            scale=10,
            maxPixels=1e13
        )

        date = image.date().format("yyyy-MM-dd").getInfo()
        ndvi_mean = ndvi_region.get('NDVI_mean').getInfo()
        ndvi_max = ndvi_region.get('NDVI_max').getInfo()
        ndvi_min = ndvi_region.get('NDVI_min').getInfo()
        ndvi_median = ndvi_region.get('NDVI_median').getInfo()
        ndvi_stdDev = ndvi_region.get('NDVI_stdDev').getInfo()

        data = {'date': date, 'ndvi_mean': ndvi_mean, 'ndvi_max': ndvi_max, 'ndvi_min': ndvi_min, 'ndvi_median': ndvi_median, 'ndvi_stdDev': ndvi_stdDev}
        all_data.append(data)

    df = pd.DataFrame(all_data)
    df = df.drop_duplicates(subset='date', keep='last')

    return df
def plot_ndvi():

    df = df_ndvi_all()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ndvi_max'],
        mode='lines',
        name='NDVI Máximo',
        marker=dict(
            color='green'
        )
    ))

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ndvi_min'],
        mode='lines',
        name='NDVI Mínimo',
        marker=dict(
            color='green'
        ),
        visible=False  # Inicialmente invisível
    ))

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ndvi_median'],
        mode='lines',
        name='NDVI Mediano',
        marker=dict(
            color='green'
        ),
        visible=False  # Inicialmente invisível
    ))

    # Atualize o layout para adicionar o menu suspenso
    fig.update_layout(
        title='Principais Valores de NDVI por registro',
        xaxis_title='Data',
        yaxis_title='NDVI',
        updatemenus=[
            dict(
                type='dropdown',
                buttons=[
                    dict(
                        label='NDVI Max',
                        method='update',
                        args=[{'visible': [True, False, False]},
                              {'title': 'NDVI Máximo'}]
                    ),
                    dict(
                        label='NDVI Min',
                        method='update',
                        args=[{'visible': [False, True, False]},
                              {'title': 'NDVI Mínimo'}]
                    ),
                    dict(
                        label='NDVI Median',
                        method='update',
                        args=[{'visible': [False, False, True]},
                              {'title': 'NDVI Mediano'}]
                    )
                ],
                direction='down',
                showactive=True
            )
        ],
        template='plotly_white'
    )

    fig.write_html("iterative_ndvi.html")

def histograma_freq():

    df = df_ndvi()

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=df['ndvi_mean'],
        nbinsx=10,  # Número de bins
        name='Histograma NDVI',
        opacity=0.75,
        marker_color='green'
    ))

    # Atualizar o layout do gráfico
    fig.update_layout(
        title='Distribuição de Valores NDVI',
        xaxis_title='NDVI',
        yaxis_title='Contagem',
        template='plotly_white'
    )

    fig.write_html("iterative_histogram.html")

def boxplot():

    df = df_ndvi()
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year

    boxplot = go.Box(
        y=df['ndvi_mean'],
        x=df['year'],
        name='NDVI',
        marker_color='green'
    )

    layout = go.Layout(
        title='Boxplot de NDVI por Ano',
        yaxis=dict(title='NDVI'),
        xaxis=dict(title='Ano'),
        template='plotly_white'
    )

    fig = go.Figure(data=[boxplot], layout=layout)

    fig.write_html("boxplot_histogram.html")

def encode_image(image_path):
    with open(image_path, 'rb') as f:
        image = f.read()
    return base64.b64encode(image).decode()

def get_montly_images():

    GoogleEarthEngine()

    roi = get_polygon()
    feature = get_ee_feature((roi))
    roi = get_ee_geometry(roi)

    start_date = datetime.strptime('2023-01-01', '%Y-%m-%d')

    dates_months = list(pd.date_range(start=start_date, periods=12, freq='1M'))
    for date in dates_months:
        s_date = date.replace(day=1).strftime('%Y-%m-%d')
        e_date = date.strftime('%Y-%m-%d')
        save_date = date.strftime('%Y%m')

        collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                      .filterBounds(roi)
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                      .filterDate(ee.Date(s_date), ee.Date(e_date)))

        collection_with_ndvi = collection.map(calculate_ndvi)

        image = collection_with_ndvi.select('NDVI')

        mediana = image.median()

        mediana = mediana.clip(feature)

        download_url = mediana.getThumbURL({
            'region': roi,
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

        print(download_url)
        response = requests.get(download_url)
        imagem = Image.open(BytesIO(response.content))

        imagem.save(f'ndvi_{save_date}.png', 'PNG')

def create_images_plot():

    start_date = datetime.strptime('2023-01-01', '%Y-%m-%d')

    dates_months = list(pd.date_range(start=start_date, periods=12, freq='1M'))
    images_path = [f"ndvi_{date.strftime('%Y%m')}.png" for date in dates_months]
    date = [f"{date.strftime('%m/%Y')}" for date in dates_months]

    df = pd.DataFrame({'images_path': images_path, 'date': date})
    df['image_base64'] = df['images_path'].apply(encode_image)

    frames = [
        go.Frame(
            data=[
                go.Image(source=f"data:image/png;base64,{row['image_base64']}")
            ],
            name=str(row['date'])
        )
        for _, row in df.iterrows()
    ]

    layout = go.Layout(
        title='Variação do NDVI em relação ao tempo',
        updatemenus=[
            {
                'buttons': [
                    {
                        'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True}],
                        'label': 'Play',
                        'method': 'animate'
                    },
                    {
                        'args': [[None], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 0}}],
                        'label': 'Pause',
                        'method': 'animate'
                    }
                ],
                'direction': 'left',
                'pad': {'r': 40, 't': 87},
                'showactive': False,
                'type': 'buttons',
                'x': 0.1,
                'xanchor': 'right',
                'y': 0,
                'yanchor': 'top'
            }
        ],
        margin=dict(l=0, r=0, t=0, b=0),
        sliders=[{
            'active': 0,
            'yanchor': 'top',
            'xanchor': 'left',
            'currentvalue': {
                'font': {'size': 20},
                'prefix': 'Data: ',
                'visible': True,
                'xanchor': 'right'
            },
            'transition': {'duration': 300, 'easing': 'cubic-in-out'},
            'pad': {'b': 10, 't': 50},
            'len': 0.9,
            'x': 0.1,
            'y': 0,
            'steps': [
                {
                    'args': [
                        [str(month)],
                        {
                            'frame': {'duration': 300, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 300}
                        }
                    ],
                    'label': str(month),
                    'method': 'animate'
                }
                for month in df['date']
            ]
        }]
    )


    fig = go.Figure(
        data=[
            go.Image(source=f"data:image/png;base64,{df.iloc[1]['image_base64']}"),
            go.Heatmap(
                z=[[0, 1], [0, 1]],
                colorscale= [
                    [0.0, 'rgb(255, 255, 255)'], [0.0625, 'rgb(206, 126, 69)'], [0.125, 'rgb(223, 146, 61)'], [0.1875, 'rgb(241, 181, 85)'],
                    [0.25, 'rgb(252, 209, 99)'], [0.3125, 'rgb(153, 183, 24)'], [0.375, 'rgb(116, 169, 1)'], [0.4375, 'rgb(102, 160, 0)'],
                    [0.5, 'rgb(82, 148, 0)'], [0.5625, 'rgb(62, 134, 1)'], [0.625, 'rgb(32, 116, 1)'], [0.6875, 'rgb(5, 98, 1)'],
                    [0.75, 'rgb(0, 76, 0)'], [0.8125, 'rgb(2, 59, 1)'], [0.875, 'rgb(1, 46, 1)'], [0.9375, 'rgb(1, 29, 1)'], [1.0, 'rgb(1, 19, 1)']
                ]
                ,
                showscale=True,
                colorbar=dict(
                    title='NDVI',
                    tickvals=[0, 0.5, 1],
                    ticktext=['-1', '0', '1'],
                    lenmode='fraction',
                    len=1,
                    thickness=18,
                    yanchor='top',
                    y=0.75,
                ),
                opacity=0
            )
        ],
        layout=layout,
        frames=frames
    )

    fig.update_layout(template="simple_white", coloraxis_showscale=True)
    fig.update_yaxes(visible=False, scaleanchor='y', scaleratio=1)
    fig.update_xaxes(visible=False)

    fig.write_html("images_slider.html")


if __name__ == '__main__':
    #display_timeseries()
    #plot_ndvi()
    #mapdisplay()
    histograma_freq()
    #boxplot()
    #get_montly_images()
    #create_images_plot()