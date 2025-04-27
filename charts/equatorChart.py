###   LINE CHART SCRIPT  -->  EQUATOR CALCULATIONS   ###


# BUBBLE CHART + DOTTED LINE + LOG2(X) + LINE CHART


# Parses the content of a JSON file representative of a pool of cities' properties and visualizes it with these dimensions:
#   - X: A city's distance to the equator       (measured in latitudes)
#   - Y: A city's temperature                   (measured in celsius)


from pandas import *
import plotly.express as px
import plotly.graph_objects as go
import json
import sys
sys.path.append('/app')
from utils import parseYmlFile

# Add necessary paths for imports
sys.path.extend(['/app/city-api', '/app/city-api/apis'])

import apis.databaseJsonApi as databaseJsonApi
import apis.mathCurveApi as mathCurveApi
import numpy as np

configPath = "/app/configuration.yml" # The fixed absolute path to the central config file


# DEVELOPER CONFIGURATIONS

dataPointSize = 14 # The size of each city's displayed bubble on the chart
dataPointOutlizeWidth = 2
highestCityTemperature = 40


# Assign configuration variables from the central 'configuration.yml' file
cities = parseYmlFile(configPath, "cities")
displayLinearTrend = parseYmlFile(configPath, "visualizations.charts.equatorChart.displayLinearTrend")
displayLogarithmicTrend = parseYmlFile(configPath, "visualizations.charts.equatorChart.displayLogarithmicTrend")
displayActualTrend = parseYmlFile(configPath, "visualizations.charts.equatorChart.displayActualTrend")
pngOutput = parseYmlFile(configPath, "visualizations.charts.equatorChart.pngOutput")
queryAttribute = parseYmlFile(configPath, "visualizations.queryConfig.queryAttribute")
queryRequirement = parseYmlFile(configPath, "visualizations.queryConfig.queryRequirement")


# Reads the pre-defined city query configurations from 'configuraiton.yml' and returns a
# descriptive string of what type of query and parameters were defined by the developer
def formatQueryConfigs():
    if queryAttribute == "continent" or queryAttribute == "timeZoneOffset":
        return f", Query: '{queryAttribute}' = '{queryRequirement}'"

    return " [DISPLAY ALL CITIES]" # No filters were selected and the developer is interacting with the entire database



def defineTrendline():

    # Indicate that no trendline will be visually displayed
    if displayLinearTrend == False and displayActualTrend == False:
        return None
    
    # If the devloper by mistake enabled both trends, then default to only displaying the actual trend and print warning message
    if displayLinearTrend == True and displayActualTrend == True:
        print("Only one linear representation is possible at a time. Either display the general linear trend or the actual trend. Set 'displayLinearTrend' or 'displayActualTrend' to False")
        return "lowess"

    if displayActualTrend == True:
        return "lowess"
    
    return "ols"



def plotEquatorChart():
    f = open('/app/city-api/apis/database/response.json')
    jsonData = json.load(f)

    xArr = databaseJsonApi.getAllAttributeInstances("equatorDistance")
    yArr = databaseJsonApi.getAllAttributeInstances("temperatureCelsius")

    # Don't plot the chart if no cities matched the developer's specified query parameters
    if len(xArr) == 0:
        print(f"No cities matches the current query filters. Change the parameters 'queryAttribute' or/and 'queryRequirement' in 'configuration.yml'")
        f.close()
        return None

    # Define color scale with explicit positions
    temperatureColorScale = [
        [0, 'rgb(0, 0, 255)'],      # Blue
        [0.25, 'rgb(0, 128, 255)'], # Light Blue
        [0.5, 'rgb(128, 128, 255)'], # Purple
        [0.75, 'rgb(255, 128, 128)'], # Light Red
        [1, 'rgb(255, 0, 0)']       # Red
    ]

    # Create base figure with explicit color scale configuration
    fig = go.Figure()

    # Add scatter plot with custom color scale
    fig.add_trace(go.Scatter(
        x=xArr,
        y=yArr,
        mode='markers',
        marker=dict(
            size=dataPointSize,
            color=yArr,  # Temperature values
            colorscale=temperatureColorScale,
            cmin=0,  # Minimum temperature
            cmax=highestCityTemperature,  # Maximum temperature
            line=dict(width=dataPointOutlizeWidth, color='DarkSlateGrey'),
            colorbar=dict(
                tickmode='array',
                ticktext=[f"{i}°C" for i in range(0, highestCityTemperature + 1, 10)],
                tickvals=[i for i in range(0, highestCityTemperature + 1, 10)],
                title=None  # Remove the title while keeping the colorbar
            )
        ),
        hovertext=[city['city'] for city in jsonData],
        hoverinfo='text+y+x'
    ))

    # Add trend line if needed
    if displayLinearTrend or displayActualTrend:
        # Calculate trend line values
        x_sorted = sorted(xArr)
        if displayActualTrend:
            # For actual trend, use a moving average
            # Ensure we have enough points for a meaningful trend
            if len(xArr) >= 2:
                # Calculate window size based on data points
                # For small datasets (2-5 points), use a small window
                # For medium datasets (6-20 points), use a medium window
                # For large datasets (20+ points), use a larger window
                if len(xArr) <= 5:
                    window_size = 2  # Small window for very small datasets
                elif len(xArr) <= 20:
                    window_size = len(xArr) // 4  # Medium window for medium datasets
                else:
                    window_size = len(xArr) // 5  # Larger window for large datasets
                
                # Ensure window size is at least 2 and not larger than dataset
                window_size = max(2, min(window_size, len(xArr) - 1))
                
                # Sort both arrays together to maintain relationship
                sorted_indices = np.argsort(xArr)
                x_sorted = np.array(xArr)[sorted_indices]
                y_sorted = np.array(yArr)[sorted_indices]
                
                # Apply moving average
                x_ma = np.convolve(x_sorted, np.ones(window_size)/window_size, mode='valid')
                y_ma = np.convolve(y_sorted, np.ones(window_size)/window_size, mode='valid')
                
                # Only use the trend if we have enough points after smoothing
                if len(x_ma) > 0 and len(y_ma) > 0:
                    trend_x = x_ma
                    trend_y = y_ma
                else:
                    # Fallback to linear trend if moving average fails
                    slope, intercept = np.polyfit(xArr, yArr, 1)
                    trend_x = x_sorted
                    trend_y = [slope * x + intercept for x in trend_x]
            else:
                # For very small datasets, use linear trend
                slope, intercept = np.polyfit(xArr, yArr, 1)
                trend_x = x_sorted
                trend_y = [slope * x + intercept for x in trend_x]
        else:
            # For linear trend, use simple linear regression
            slope, intercept = np.polyfit(xArr, yArr, 1)
            trend_x = x_sorted
            trend_y = [slope * x + intercept for x in trend_x]
        
        # Add trend line trace
        fig.add_trace(go.Scatter(
            x=trend_x,
            y=trend_y,
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.7)', width=2, dash='dash'),
            name=f"{'Actual' if displayActualTrend else 'Linear'} Trend"
        ))

    # Update layout
    fig.update_layout(
        title=f"Cities: Equator Distance vs Temperature{formatQueryConfigs()}",
        xaxis_title="Equator Distance (latitudes)",
        yaxis_title="Temperature (Celsius)",
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    # If developer wants to plot the logarithmic trend, merge it with the main figure
    if displayLogarithmicTrend == True:
        logTrendFig = getexpectedLogarithmicTrend()
        finalFig = go.Figure(data=fig.data + logTrendFig.data)
        
        # Preserve layout settings
        finalFig.update_layout(fig.layout)
        
        if pngOutput == True:
            exportPng(finalFig, getTypeOfQueryString(), getPngOutputString())
            
        f.close()
        return finalFig.to_json()
    else:
        if pngOutput == True:
            exportPng(fig, getTypeOfQueryString(), getPngOutputString())
            
        f.close()
        return fig.to_json()


# Fetches the data from the API and plots it on a graph
def getexpectedLogarithmicTrend():
    logarithmicCurveData = mathCurveApi.getDataArrays(highestCityTemperature)
    # Create a line plot with a specific color that complements the scatter plot
    fig1 = px.line(logarithmicCurveData, x="equatorDistance", y="temperatureCelsius", 
                   color_discrete_sequence=['rgba(255, 255, 255, 0.7)'])  # White line with transparency
    
    # Make the line dashed for better visibility
    fig1.update_traces(line=dict(dash='dash', width=2))
    
    return fig1



def exportPng(figure, typeOfQuery, fileOutputName):
    figure.write_image(f"/app/city-api/generated-artifacts/pngs/equator-chart/{typeOfQuery}/{fileOutputName}.png")



# Returns the name the output of the to-be produced .png file. The name
# represents the selected settings that the developer configured in
# configuration.yml
def getPngOutputString():

    str1 = "Linear Trend" if displayLinearTrend == True else ""
    str2 = "Logarithmic Trend" if displayLogarithmicTrend == True else ""
    str3 = "Actual Trend" if displayActualTrend == True else ""

    trendStringSum = len(str1) + len(str2) + len(str3)

    noTrendStr = "No trend" if trendStringSum == 0 else ""

    if len(noTrendStr) > 0:
        return f"Equator Chart [{noTrendStr}]"
    
    trendStrings = [str1, str2, str3]
    outputStr = "Equator Chart ["

    for currentStr in trendStrings:
        if len(currentStr) > 0:
            outputStr += currentStr + ", "

    outputStr += "]"

    return outputStr


# Checks the query attribute and returns it in a format coherent with the subfolders
# of the chart-png outputs that divides equator charts into query-categories
def getTypeOfQueryString():
    if queryAttribute == "continent":
        return "continent-queries"
    elif queryAttribute == "timeZoneOffset":
        return "timezone-queries"
    return "none-filter-queries"