from pandas import *
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from operator import itemgetter 
import sys
import os
import json
import numpy as np
from datetime import datetime

sys.path.append('/app')

import apis.colorApi as colorApi
from utils import parseYmlFile

# Configuration file path
configPath = "/app/configuration.yml"

# Get cities from configuration
cities = parseYmlFile(configPath, "cities")

# Number of latest readings to show
N_LATEST_READINGS = 10

# Custom color palette for better visuals
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

# Read data from CSV files
data = []
city_sums = {}
latest_timestamps = {}

for city in cities:
    try:
        df = pd.read_csv(f"/app/city-api/generated-artifacts/csvs/{city}.csv")
        # Convert timestamp to datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').tail(N_LATEST_READINGS)
        
        avg_temp = df['average_temperature'].mean()
        sum_temp = df['average_temperature'].sum()
        latest_timestamps[city] = df['timestamp'].max()
        
        data.append({
            'city': city,
            'temperature': avg_temp,
            'latest_timestamp': latest_timestamps[city]
        })
        city_sums[city] = sum_temp
    except Exception as e:
        print(f"Error reading data for {city}: {e}")

if not data:
    print("No data available to create charts")
    sys.exit(1)

# Get the 4 coldest cities
num_coldest = min(4, len(city_sums))
coldest_cities = dict(sorted(city_sums.items(), key=itemgetter(1))[:num_coldest])

# Create main pie chart
df = pd.DataFrame(data)
cities_list = df['city'].values.tolist()
temperatures_list = df['temperature'].values.tolist()

fig1 = go.Figure(data=[go.Pie(
    labels=cities_list,
    values=temperatures_list,
    hole=0.3,
    textinfo='label+percent',
    textposition='outside',
    pull=[0.1 if city in coldest_cities else 0 for city in cities_list],
    marker=dict(
        colors=[color_palette.get(city, '#FF9F1C') for city in cities_list],
        line=dict(color='white', width=2)
    ),
    hovertemplate="<b>%{label}</b><br>" +
                  "Temperature: %{value:.1f}°C<br>" +
                  "<extra></extra>"
)])

# Format the latest timestamp for display
latest_time = max(latest_timestamps.values()).strftime('%Y-%m-%d %H:%M:%S')

fig1.update_layout(
    title=dict(
        text=f'Temperature Distribution Across All Cities<br><sub>Last {N_LATEST_READINGS} readings per city</sub>',
        x=0.5,
        y=0.95,
        xanchor='center',
        yanchor='top',
        font=dict(size=24, color='#2B2D42')
    ),
    showlegend=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(t=100, b=50, l=50, r=50),
    annotations=[
        dict(
            text=f"Last updated: {latest_time}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.1,
            showarrow=False,
            font=dict(size=12)
        )
    ]
)

# Create coldest cities pie chart
coldest_data = [{'city': city, 'temperature': temp} for city, temp in coldest_cities.items()]
df_coldest = pd.DataFrame(coldest_data)
coldest_cities_list = df_coldest['city'].values.tolist()
coldest_temps_list = df_coldest['temperature'].values.tolist()

cold_colors = ['#A8E6CF', '#DCEDC1', '#FFD3B6', '#FFAAA5']  # Cool, calming colors
fig2 = go.Figure(data=[go.Pie(
    labels=coldest_cities_list,
    values=coldest_temps_list,
    hole=0.3,
    textinfo='label+percent',
    textposition='outside',
    marker=dict(
        colors=cold_colors[:len(df_coldest)],
        line=dict(color='white', width=2),
        pattern=dict(
            shape=['/', '\\', 'x', '+'][:len(df_coldest)]
        )
    ),
    hovertemplate="<b>%{label}</b><br>" +
                  "Total Temperature: %{value:.1f}°C<br>" +
                  "<extra></extra>"
)])

fig2.update_layout(
    title=dict(
        text=f'4 Coldest Cities Temperature Distribution<br><sub>Based on last {N_LATEST_READINGS} readings</sub>',
        x=0.5,
        y=0.95,
        xanchor='center',
        yanchor='top',
        font=dict(size=24, color='#2B2D42')
    ),
    showlegend=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(t=100, b=50, l=50, r=50),
    annotations=[
        dict(
            text=f"Last updated: {latest_time}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.1,
            showarrow=False,
            font=dict(size=12)
        )
    ]
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
        return json.JSONEncoder.default(self, obj)

# Create an HTML file with both charts side by side
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        .chart-container {{
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            margin: 0;
        }}
        .chart {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            width: 45%;
            transition: all 0.3s ease;
        }}
        .chart:hover {{
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
<body style="margin: 0; padding: 0;">
    <div class="chart-container">
        <div class="chart" id="chart1"></div>
        <div class="chart" id="chart2"></div>
    </div>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        var chart1 = {json.dumps(fig1.to_dict(), cls=NumpyEncoder)};
        var chart2 = {json.dumps(fig2.to_dict(), cls=NumpyEncoder)};
        let updateCount = 0;
        
        function initCharts() {{
            Plotly.newPlot('chart1', chart1.data, chart1.layout, {{
                responsive: true,
                displayModeBar: false,
                staticPlot: false
            }});
            Plotly.newPlot('chart2', chart2.data, chart2.layout, {{
                responsive: true,
                displayModeBar: false,
                staticPlot: false
            }});
        }}

        async function updateCharts() {{
            try {{
                const response = await fetch(window.location.href);
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const scripts = doc.querySelectorAll('script');
                let newChart1, newChart2;
                
                for (const script of scripts) {{
                    if (script.textContent.includes('chart1')) {{
                        const match = script.textContent.match(/var chart1 = (.*?);/);
                        if (match) newChart1 = JSON.parse(match[1]);
                    }}
                    if (script.textContent.includes('chart2')) {{
                        const match = script.textContent.match(/var chart2 = (.*?);/);
                        if (match) newChart2 = JSON.parse(match[1]);
                    }}
                }}

                if (newChart1 && newChart2) {{
                    updateCount++;
                    
                    // Optimize animation based on update count
                    const duration = 150; // Faster transitions
                    
                    // Update chart1 with optimized animation
                    await Plotly.animate('chart1', {{
                        data: newChart1.data,
                        layout: newChart1.layout
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

                    // Update chart2 with optimized animation
                    await Plotly.animate('chart2', {{
                        data: newChart2.data,
                        layout: newChart2.layout
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
                    const charts = document.querySelectorAll('.chart');
                    charts.forEach(chart => {{
                        chart.classList.remove('updating');
                        void chart.offsetWidth; // Force reflow
                        chart.classList.add('updating');
                    }});
                }}
            }} catch (error) {{
                console.error('Error updating charts:', error);
            }}
        }}
        
        initCharts();
        // Update every 200ms
        setInterval(updateCharts, 200);
    </script>
</body>
</html>
"""

with open("/app/public/pie_charts.html", "w") as f:
    f.write(html_content)

chartTypes = ['Random-Colors', '4-Coldest-Cities', 'Color-Theme'] # Available options

## PIE CHART CONFIGURATIONS  ##
selectedChartType = parseYmlFile(configPath, "visualizations.charts.pieChart.chartType")
colorTheme = parseYmlFile(configPath, "visualizations.charts.pieChart.pieColorTheme")

def getCitySums():
    output = {}
    for city in cities:
        df2 = pd.read_csv(f"/app/city-api/generated-artifacts/csvs/{city}.csv")
        currentCitySum = df2['average_temperature'].sum()
        output[city] = currentCitySum
    return output

def plotRandomColoredChart(cityTemperatureSums):
    citySumsArray = list(cityTemperatureSums.values())
    fig = go.Figure(data=[go.Pie(labels=cities, values=citySumsArray, textinfo='label+percent',
                                insidetextorientation='radial')])
    fig.show()
    if pngOutput == True:
        exportPng(fig, "random-colors/random-colors-now")

def plot4HottestCities(cityTemperatureSums):
    numCities = min(4, len(cities))
    hottestCities = getColdestCities(cityTemperatureSums, numCities)
    cityNames = list(hottestCities.keys())
    citySums = list(hottestCities.values())
    colors = ["gold", "mediumturquoise", "darkorange", "lightgreen"]
    resultingColors = colors[:numCities]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=cityNames,
                values=citySums,
                textfont_size=20,
                marker=dict(colors=resultingColors, pattern=dict(shape=[".", "x", "+", "-"]))
            )
        ]
    )
    fig.show()
    if pngOutput == True:
        exportPng(fig, "4-coldest/4-coldest-now")

def getColdestCities(inputDictionary, n):
    hottestCities = dict(sorted(inputDictionary.items(), key=itemgetter(1))[:n])
    return hottestCities

def plotColorThemedChart(cityTemperatureSums):
    cityColorMapping = colorApi.getCityChartColors(colorTheme)
    citySumsArray = list(cityTemperatureSums.values())
    fig = px.pie(values=citySumsArray, names=cities, color=cities,
                color_discrete_map=cityColorMapping)
    fig.show()
    if pngOutput == True:
        exportPng(fig, f"color-theme/all-cities [{colorTheme.upper()} THEME]")

def exportPng(figure, fileOutputName):
    figure.write_image(f"/app/city-api/generated-artifacts/pngs/pie-chart/{fileOutputName}.png")

def plotPieChart():
    cityTemperatureSums = getCitySums()
    if selectedChartType == chartTypes[0]:
        return plotRandomColoredChart(cityTemperatureSums)
    elif selectedChartType == chartTypes[1]:
        return plot4HottestCities(cityTemperatureSums)
    else:
        plotColorThemedChart(cityTemperatureSums)

def create_pie_chart():
    selectedChartType = parseYmlFile(configPath, "visualizations.charts.pieChart.chartType")
    colorTheme = parseYmlFile(configPath, "visualizations.charts.pieChart.pieColorTheme")