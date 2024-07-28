import pandas as pd
import matplotlib.pyplot as plt
import geemap.foliumap as geemap
import plotly.graph_objs as go
from datetime import datetime
import ee

from src.data_processing import DataProcessor

plt.style.use('seaborn-v0_8-whitegrid')

class NDVIVisualization:
    def __init__(self, df_data: pd.DataFrame, start_date, feature):
        self.df_data = df_data
        self.start_date = start_date
        self.feature = feature
    def plot_timeseries(self):
        """Geração de um gráfico de linha com motplotlib. Considera os valores médios do NDVI de todos os registros do período"""
        self.df_data['date'] = pd.to_datetime(self.df_data['date'], format='%Y-%m-%d')
        self.df_data['date'] = self.df_data['date'].dt.strftime('%d/%m/%Y')

        plt.figure(figsize=(12, 6))
        plt.plot(self.df_data['date'], self.df_data['ndvi_mean'], marker='o', linestyle='-', color='g', markersize=8, linewidth=2, label='NDVI Médio')

        plt.title('Evolução da Média de NDVI', fontsize=16, fontweight='bold')
        plt.xlabel('Data', fontsize=14)
        plt.ylabel('NDVI Médio', fontsize=14)

        plt.ylim(-1, 1)

        plt.xticks(rotation=45, ha='right', fontsize=12)
        plt.yticks(fontsize=12)

        plt.grid(True, linestyle='--', alpha=0.7)

        plt.legend()

        for i, row in self.df_data.iterrows():
            plt.text(row['date'], row['ndvi_mean'] + 0.04, f'{row["ndvi_mean"]:.2f}', ha='center', fontsize=10)

        plt.tight_layout()

        plt.savefig("data/results/temporal_ndvi_mean.png", format='png')

    def plot_ndvi_data(self):
        """Gera um gráfico dinâmico com os valores de Max, Min e Mediana de todos os registros do período"""
        fig = go.Figure()

        df_data = pd.DataFrame()

        df_data['ndvi_max'] = self.df_data['ndvi_max'].interpolate()
        df_data['ndvi_min'] = self.df_data['ndvi_min'].interpolate()
        df_data['ndvi_median'] = self.df_data['ndvi_median'].interpolate()
        df_data['date'] = self.df_data['date']

        fig.add_trace(go.Scatter(
            x=df_data['date'],
            y=df_data['ndvi_max'],
            mode='lines',
            name='NDVI Máximo',
            marker=dict(
                color='green'
            )
        ))

        fig.add_trace(go.Scatter(
            x=df_data['date'],
            y=df_data['ndvi_min'],
            mode='lines',
            name='NDVI Mínimo',
            marker=dict(
                color='green'
            ),
            visible=False
        ))

        fig.add_trace(go.Scatter(
            x=df_data['date'],
            y=df_data['ndvi_median'],
            mode='lines',
            name='NDVI Mediano',
            marker=dict(
                color='green'
            ),
            visible=False
        ))

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

        fig.write_html("data/results/iterative_ndvi.html")

    def plot_histograma_freq(self):
        """Gera um histograma de frequência de todos os valores médios de NDVI registrados no período"""
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=self.df_data['ndvi_mean'],
            nbinsx=10,
            name='Histograma NDVI',
            opacity=0.75,
            marker_color='green'
        ))

        fig.update_layout(
            title='Distribuição de Valores Médios de NDVI',
            xaxis_title='NDVI',
            yaxis_title='Contagem',
            template='plotly_white'
        )

        fig.write_html("data/results/iterative_histogram.html")

    def plot_boxplot(self):
        """Gera um bozplot com os valores médios de NDVI registrados, agrupados por ano"""
        self.df_data['date'] = pd.to_datetime(self.df_data['date'], dayfirst=True)
        self.df_data['year'] = self.df_data['date'].dt.year

        boxplot = go.Box(
            y=self.df_data['ndvi_mean'],
            x=self.df_data['year'],
            name='NDVI',
            marker_color='green'
        )

        layout = go.Layout(
            title='Boxplot de NDVI Médio por Ano',
            yaxis=dict(title='NDVI'),
            xaxis=dict(title='Ano'),
            template='plotly_white'
        )

        fig = go.Figure(data=[boxplot], layout=layout)

        fig.write_html("data/results/iterative_boxplot.html")

    def plot_images_timelapse(self):
        """Gera um timelapse com o heatmap da propriedade referente os valores de Mediana Mensal do NDVI"""
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        dates_months = list(pd.date_range(start=start_date, periods=12, freq='1M'))

        images_path = [f"data/results/ndvi_{date.strftime('%Y%m')}.png" for date in dates_months]
        date = [f"{date.strftime('%m/%Y')}" for date in dates_months]

        self.df_data = pd.DataFrame({'images_path': images_path, 'date': date})
        self.df_data['image_base64'] = self.df_data['images_path'].apply(DataProcessor.encode_image)

        frames = [
            go.Frame(
                data=[
                    go.Image(source=f"data:image/png;base64,{row['image_base64']}")
                ],
                name=str(row['date'])
            )
            for _, row in self.df_data.iterrows()
        ]

        layout = go.Layout(
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
                    for month in self.df_data['date']
                ]
            }]
        )


        fig = go.Figure(
            data=[
                go.Image(source=f"data:image/png;base64,{self.df_data.iloc[1]['image_base64']}"),
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

        fig.write_html("data/results/images_slider.html")

    def plot_mapdisplay(self):
        """Gera um mapa dinâmico mostrando a área da propriedade"""
        m = geemap.Map()
        m.add_basemap('SATELLITE')

        features = ee.FeatureCollection([self.feature])

        style = {
            'color': 'red',
            'width': 4,
            'fillColor': '00000000'
        }
        styled_polygon = features.style(**style)

        m.addLayer(styled_polygon, {}, 'Fazenda Batista')

        m.centerObject(self.feature, zoom=15)
        m.to_html(filename='data/results/map.html')