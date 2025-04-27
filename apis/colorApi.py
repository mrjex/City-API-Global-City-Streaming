import requests

cities = [
    'London', 'Stockholm', 'Toronto', 'Moscow', 'Madrid',
    'Reykjavik', 'Helsinki', 'Rome', 'Venice', 'Lisbon',
    'Paris', 'Amsterdam', 'Chernobyl', 'Nairobi', 'Dubai',
    'Bali', 'Paris', 'Tokyo', 'Bangkok', 'Seoul',
    'Buenos Aires', 'Mexico City'
  ]



# Color API Website: https://www.csscolorsapi.com/


def fetchApiData(color):
   apiUrl = f"https://www.csscolorsapi.com/api/colors/group/{color}"

   response = requests.get(apiUrl)
   body_dict = response.json()

   colors = body_dict['colors']
   return colors


# Returns a dictionary:
#  - key: city name (e.g 'London')
#  - value: rgb color (e.g 'rgb(255, 240, 245)')
def mapCityChartColors(apiResponse, numColors):
   output = {}

   for i in range(len(cities)):
      currentRgb = apiResponse[i % numColors]['rgb']
      currentCity = cities[i]

      output[currentCity] = formatRgb(currentRgb)
   
   return output


   #numIterations = min(len(cities), numColors) # The mapping is bounded by the two arrays' parallel dependency

   #for i in range(numIterations):
   #   currentRgb = apiResponse[i]['rgb']
   #   currentCity = cities[i]
   #   
   #   output[currentCity] = formatRgb(currentRgb)

   #return output


# Formats the RGB response fetched from the API to match the expected string-structure
# that plotly's scatter plot class expects (referencing the code in bubble-chart.py).
# This function performs the following operation:
#  '139,0,139'   -->   rgb(139,0,139)
def formatRgb(rgbInput):
   formattedStr = ''.join(('rgb(',f"{rgbInput}",')'))
   return formattedStr


# Sends a request to the Color-API and uses the response to return a dictionary with the following  format:
#     -  key: Distinct city (e.g 'Madrid')
#     -  value: The RGB color that will be used when plotting all
#        the city's datapoints (e.g 'rgb(186,85,211)')
def getCityChartColors(color):
   apiColorResponse = fetchApiData(color)
   numColors = len(apiColorResponse)

   chartColorDictionary = mapCityChartColors(apiColorResponse, numColors)

   # print(chartColorDictionary)
   # print(chartColorDictionary['Rome'])

   return chartColorDictionary



# Returns a two dimensional array. Each inner-array consists of two elements:
#     - PERCENTAGE:  A decimal value between 0.0 and 1.0. The first inner-array
#                    will always equate to 0.0, and the last one 1.0. I.e the
#                    arrays are stored in an ascending order.
#
#     - HEXCOLOR:    The associated color of each percentage-value. For example
#                    '#1b0c41' and '#fb9b06'
#
#  For clarification, here is the output format:
#  [
#     [PERCENTAGE, HEXCOLOR], ..., [PERCENTAGE, HEXCOLOR]
#  ]
def generateColorScale(): # TODO: Generalize this and document my mathematical reasoning and elication of the formula
   
   # fixedColorScale = [] # For now it is fixed

   colorscale = [
      [0, '#cf4446'], 
      [0.5, '#151b99'],
      [1, '#a2faac']
   ]

   return colorscale