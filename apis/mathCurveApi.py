###   MATH CURVE API   ###

# Has the single responsibility of returning responses related to coherent data.
# This is done through back-end calculations whose results are forwarded to
# the requesting software instances, and lastly plotted on a visual graph.


# The entry point of this script is 'getDataArrays()' which is invoked
# from '/charts/equatorChart.py'.

# The returned data is concerned with the expected (my hypothesis)
# general trend of the city-data-points


import math

# FORMULA:   y = a * loge(-0.5x + 45) + 5

xShiftLog = -0.5 # The multiplier of x in the loge()
additionalYShift = 5 # The last addition to modify the y-axis placement of the graph
xShift = 45



def getCurveSlope(maxCityTemperature):
    x = 0
    logVal = (xShiftLog * x) + xShift # The final value inside the parenthesis of loge()

    yResolution = maxCityTemperature - additionalYShift # Move right-sides terms to the left hand side of the mathematical equation

    a = yResolution / math.log(logVal, math.e) # Move 'yResolution' to the right side to resolve the 'curveSlope' variable
    return a



# Returns a key-value structure of the data to be plotted.
# 'xArr' and 'yArr' are both one-dimensional arrays of numerical
# values with equal lengths.
def getDataArrays(maxCityTemperature):
    a = getCurveSlope(maxCityTemperature)


    # FORMULA:   y = a * loge(-0.5x + 45) + 5

    xArr = []
    yArr = []


    # The graph will always have 90 x-values since the maximal absolute distance from
    # the equator is abs(90) = 90 and abs(-90) = 90.
    for x in range(90):
        xArr.append(x)
        product = a * math.log((xShiftLog * x) + xShift) + additionalYShift
        yArr.append(product)
    

    dataResponse = {
        "equatorDistance": xArr,
        "temperatureCelsius": yArr
    }
    
    return dataResponse
