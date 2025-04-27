# Generates bubble-charts that compares the different cities' differences
# in temperature for each API-Call. You as a developer can select the
# output format as follows:
#
#   - Boolean 'seperateGraphDisplay':
#       - True: Generates N different bubble-chart plots, where N is the
#         number of distinct cities
#       
#       - False: Generates one bubble-chart plot with N different categories.
#                Each category is distinguished by its unique RGB color.



from pandas import *
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import json
import numpy as np
from datetime import datetime, timedelta
import pandas as pd


sys.path.append('/app')
from utils import parseYmlFile

sys.path.append('/app/city-api')
import apis.colorApi as colorApi


configPath = "/app/configuration.yml" # The fixed relative path to the central config file


pngOutput = parseYmlFile(configPath, "visualizations.charts.bubbleChart.pngOutput")
colorTheme = parseYmlFile(configPath, "visualizations.charts.bubbleChart.bubbleColorTheme")
separateGraphDisplay = parseYmlFile(configPath, "visualizations.charts.bubbleChart.separateGraphDisplay")
 

##  OUTPUT FORMAT  ##
# pngOutput = True
# separateGraphDisplay = False
# colorTheme = "yellow"


dataPointSize = 11 # The size of each city's displayed bubble on the chart
dataPointOutlizeWidth = 0




cities = parseYmlFile(configPath, "realTimeProduction.cities")



cityFigures = []



# Separately generates all graphs for each city and stores them as
# 'figure' variables inside 'cityFigures' array
def generateCityGraphs():

    cityColorMapping = colorApi.getCityChartColors(colorTheme)

    for city in cities:
        data = read_csv(f"/app/city-api/generated-artifacts/csvs/{city}.csv")
        currentColor = cityColorMapping[city]

        currentCityFigure = px.scatter(data, x="API-Call", y="average_temperature",
                color="city",
                    hover_name="city", log_x=True, size_max=60,
                    color_discrete_sequence=[currentColor])

        currentCityFigure.update_traces(
                    marker=dict(size=dataPointSize,
                    line=dict(width=dataPointOutlizeWidth,
                    color='DarkSlateGrey')),
                    selector=dict(mode='markers')
                )
       
        cityFigures.append(currentCityFigure)



def mergeGraphs():
    data = cityFigures[0].data

    for i in range(1, len(cityFigures)):
        data  += cityFigures[i].data
    
    mergedGraph = go.Figure(data)


    mergedGraph.update_layout(
        title="City Temperatures",
        xaxis_title="N:th Weather API Response",
        yaxis_title="Average Temperature",
        legend_title="Cities",
        font=dict(
            family="Courier New, monospace",
            size=18,
            color="RebeccaPurple"
        )
    )
    
    if pngOutput == True:
        exportPng(mergedGraph, f"all-cities [{colorTheme.upper()} THEME]")

    mergedGraph.show()


def displaySeparateGraphs():
    for i in range(len(cityFigures)):

        if pngOutput == True:
            exportPng(cityFigures[i], f"{cities[i]}, [{colorTheme.upper()} THEME]")

        cityFigures[i].show()



def exportPng(figure, fileOutputName):
    figure.write_image(f"/app/public/bubble-chart/{fileOutputName}.png")


def plotBubbleChart():
    generateCityGraphs()

    if separateGraphDisplay:
        displaySeparateGraphs()
    else:
        mergeGraphs()

# Configuration
configPath = "/app/configuration.yml"
cities = parseYmlFile(configPath, "realTimeProduction.cities")

# Number of latest readings to show in the sliding window
N_LATEST_READINGS = 10  # Reduced from 20 to 10 for smoother updates

# Custom color palette
color_palette = {
    'Bangkok': '#FF6B6B',    # Coral Red
    'Lisbon': '#4ECDC4',     # Turquoise
    'Paris': '#45B7D1',      # Ocean Blue
    'Dubai': '#96CEB4',      # Sage Green
    'Tokyo': '#FFBE0B',      # Amber
    'London': '#3D405B',     # Navy Blue
    'Moscow': '#E63946',     # Imperial Red
    'Madrid': '#588B8B'      # Teal
}

# Read and process data
def get_city_data(city):
    try:
        df = pd.read_csv(f"/app/city-api/generated-artifacts/csvs/{city}.csv")
        # Convert timestamp to datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').tail(N_LATEST_READINGS)
        return df
    except Exception as e:
        print(f"Error reading data for {city}: {e}")
        return None

# Create traces for each city
traces = []
for city in cities:
    df = get_city_data(city)
    if df is not None and len(df) > 0:
        try:
            # Calculate bubble size based on temperature range
            min_temp = df['average_temperature'].min()
            max_temp = df['average_temperature'].max()
            if min_temp == max_temp:
                size = [20] * len(df)  # Use constant size if all temperatures are the same
            else:
                size = 20 + (df['average_temperature'] - min_temp) / (max_temp - min_temp) * 30
            
            trace = go.Scatter(
                name=city,
                x=df['timestamp'],
                y=df['average_temperature'],
                mode='markers+lines',
                marker=dict(
                    size=size if isinstance(size, list) else size.tolist(),
                    sizemode='area',
                    sizeref=2.*max(size if isinstance(size, list) else size)/(40.**2),
                    color=color_palette.get(city, '#FF9F1C'),
                    line=dict(color='white', width=1)
                ),
                line=dict(color=color_palette.get(city, '#FF9F1C')),
                hovertemplate="<b>%{text}</b><br>" +
                             "Temperature: %{y:.1f}°C<br>" +
                             "Time: %{x}<br>" +
                             "<extra></extra>",
                text=[city] * len(df)
            )
            traces.append(trace)
        except Exception as e:
            print(f"Error processing data for {city}: {e}")

if not traces:
    print("No data available to create chart")
    sys.exit(1)

# Create the figure
fig = go.Figure(data=traces)

# Update layout
fig.update_layout(
    title=dict(
        text=f'Real-time Temperature Trends<br><sub>Showing last {N_LATEST_READINGS} readings per city</sub>',
        x=0.5,
        y=0.95,
        xanchor='center',
        yanchor='top',
        font=dict(size=24, color='#2B2D42')
    ),
    xaxis=dict(
        title='Time',
        gridcolor='#E5E5E5',
        showgrid=True,
        type='date',
        tickformat='%Y-%m-%d %H:%M:%S'
    ),
    yaxis=dict(
        title='Temperature (°C)',
        gridcolor='#E5E5E5',
        showgrid=True
    ),
    plot_bgcolor='white',
    paper_bgcolor='white',
    hovermode='closest',
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.05
    ),
    margin=dict(t=100, b=50, l=50, r=150)
)

# Custom JSON encoder for NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.float32):
            return float(obj)
        if isinstance(obj, np.int64):
            return int(obj)
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return json.JSONEncoder.default(self, obj)

# Create HTML with auto-refresh and animations
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}
        #chart {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            transition: all 0.3s ease;
        }}
        #chart:hover {{
            transform: translateY(-5px);
        }}
        @keyframes pulse {{
            0% {{ box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
            50% {{ box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2); }}
            100% {{ box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
        }}
        .updating {{
            animation: pulse 0.4s ease-in-out;
        }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        var chartData = {json.dumps(fig.to_dict(), cls=NumpyEncoder)};
        let updateCount = 0;
        
        function initChart() {{
            Plotly.newPlot('chart', chartData.data, chartData.layout, {{
                responsive: true,
                displayModeBar: false,
                staticPlot: false
            }});
        }}

        async function updateChart() {{
            try {{
                const response = await fetch(window.location.href);
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newChartData = JSON.parse(doc.querySelector('script').textContent.match(/var chartData = (.*?);/)[1]);
                
                updateCount++;
                const duration = 150; // Faster transitions
                
                // Optimize animation
                await Plotly.animate('chart', {{
                    data: newChartData.data,
                    layout: newChartData.layout
                }}, {{
                    transition: {{
                        duration: duration,
                        easing: 'cubic-in-out'
                    }},
                    frame: {{
                        duration: duration,
                        redraw: false
                    }}
                }});

                // Add subtle visual feedback
                const chart = document.getElementById('chart');
                chart.classList.remove('updating');
                void chart.offsetWidth; // Force reflow
                chart.classList.add('updating');
            }} catch (error) {{
                console.error('Error updating chart:', error);
            }}
        }}
        
        initChart();
        // Update every 200ms
        setInterval(updateChart, 200);
    </script>
</body>
</html>
"""

with open("/app/public/bubble_chart.html", "w") as f:
    f.write(html_content)