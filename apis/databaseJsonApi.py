# Json database manager

# Solely dedicated for the equator chart visualization

#   - queryApi.py + cityApi.py
#   - a composition of Weather API & Timezone API

import sys

# Add necessary paths for imports
sys.path.extend(['/app/city-api', '/app/city-api/apis', '/app'])

import apis.geolocationApi as geolocationApi
from shared.weather.api import WeatherAPI
import json
from utils import parseYmlFile

print("Starting databaseJsonApi.py...")
print(f"Current working directory: {sys.path}")

configPath = "/app/configuration.yml"
print(f"Reading config from: {configPath}")

# Initialize the shared WeatherAPI
weather_api = WeatherAPI()

# In shell scripts where this script is combined with other scripts to create a bigger sequence of automation,
# the path below is used from the invoking point to this file
databasePath = "/app/city-api/apis/database/db.json"
print(f"Database path: {databasePath}")


# The query-file paths for "/logs" directory
#   - Key: The attribute to query
#   - Value: The path to the query's associated json-log file
databaseLogPaths = {
    "continent": "/app/city-api/apis/database/logs/query-continents.json",
    "timeZoneOffset": "/app/city-api/apis/database/logs/query-timezones.json"
}


# READ DEVELOPER DEBUG CONFIGURATIONS from 'configuration.yml'
cities = parseYmlFile(configPath, "cities")
queryAttribute = parseYmlFile(configPath, "visualizations.queryConfig.queryAttribute")
queryRequirement = parseYmlFile(configPath, "visualizations.queryConfig.queryRequirement")
print(f"Query config loaded - {queryAttribute}: {queryRequirement}")


# This function composes each JSON object for all the cities
def populateDB():
  citiesArr = [] # An array that gets assigned the dictionary-object for each city in the loop below

  for city in cities:
    # Read the data from the APIs
    weatherCityObj = weather_api.fetch_city_data(city)
    timezoneDictionary = geolocationApi.fetchTimeZoneData(weatherCityObj['latitude'], weatherCityObj['longitude'])

    equatorDistanceAttribute = abs(weatherCityObj['latitude'])

    # Compose the data into new dictionary that holds the values
    # of the city's data in the current iteration
    currentCityObj = weatherCityObj

    # Assign the fetched and calculated attributes to the new object
    currentCityObj['timeZoneNotation'] = timezoneDictionary['timeZoneNotation']
    currentCityObj['timeZoneOffset'] = timezoneDictionary['timeZoneOffset']
    currentCityObj['equatorDistance'] = equatorDistanceAttribute

    citiesArr.append(currentCityObj)

  # Store the cities and their information as objects in a JSON file
  with open(databasePath, "w") as outfile: 
    json.dump(citiesArr, outfile, indent=4)

  return citiesArr



# FUNCTION:
#   - Iterates over all db-instances and only writes to (or updates) the instances stored in
#     the JSON files in which the target attribute satisfies the given requirement
#
# PARAMETERS:
#   - queryAttribute:     The name of the attribute in a city object
#   - queryRequirement:   The required value for a city's object to obtain
#
# EXAMPLE INPUTS:
#   - ("continent", "Europe")
#   - ("continent", "Asia")
#
#   - ("timeZoneOffset", "UTC+1")
#   - ("timeZoneOffset", "UTC-6")
#
def queryByAttribute(attributeToQuery, queryRequirement):
    outputJsonFile = databaseLogPaths[attributeToQuery]
    
    try:
        with open(databasePath) as f:
            jsonDB = json.load(f)

        matchedObjects = []
        for cityObj in jsonDB:
            if cityObj[attributeToQuery] == queryRequirement:
                matchedObjects.append(cityObj)
        
        print(f"\nQuery results for {attributeToQuery}={queryRequirement}:")
        print(json.dumps(matchedObjects, indent=2))

        # Update "/log" json file
        with open(outputJsonFile, "w") as outfile:
            json.dump(matchedObjects, outfile, indent=4)
        
        # Always update 'response.json'
        responsePath = "/app/city-api/apis/database/response.json"
        with open(responsePath, "w") as outfile:
            json.dump(matchedObjects, outfile, indent=4)
            
    except Exception as e:
        print(f"Error in queryByAttribute: {str(e)}")



# Returns a one-dimensional array of all instances of a specific attribute.
# This is done by querying 'response.json' and for each city-object, append
# the specified attribute's value
def getAllAttributeInstances(attribute):
  return getCitiesAttribute(attribute)



# Returns an array of each cities' value tied to the key named 'attribute'.
# A few possible values for 'attribute' are "equatorDisance",
# "temperatureCelsius", "latitude", "continent" (referencing
# to the values in 'db.json')
def getCitiesAttribute(attribute):

    output = []

    f = open("/app/city-api/apis/database/response.json") # Path is "city-api\charts", since it's called from 'equator-chart.py'
    data = json.load(f)

    numInstances = len(data)
    getCityAttribute = lambda data, i, attribute : data[i][f"{attribute}"]

    for i in range(numInstances):
        output.append(getCityAttribute(data, i, attribute))
    

    f.close()
    return output



# Returns the JSON object that obtains the inputted city name
def getCityObject(targetCity):
    f = open(f"{databasePath}")
    data = json.load(f)

    citiesPoolNum = len(data)

    for i in range(citiesPoolNum):
        cityObj = data[i]

        # Return the city's object if it was found in the .json database
        if cityObj['city'] == targetCity:
           return cityObj
    
    return f"The city '{targetCity}' isn't in the cities pool"




# Developer chooses to not apply any filter-conditions and retrieves all city objects
# Essentially, what this function does is to transfer the content from 'db.json' to
# 'respone.json'
def getAllCities():
    try:
        with open(databasePath) as f:
            jsonDB = json.load(f)
            print("\nRetrieving all cities:")
            print(json.dumps(jsonDB, indent=2))

        responsePath = "/app/city-api/apis/database/response.json"
        with open(responsePath, "w") as outfile:
            json.dump(jsonDB, outfile, indent=4)
    except Exception as e:
        print(f"Error in getAllCities: {str(e)}")



# Generates the JSON database instances and queries them  -->  EquatorChart
def initiateDatabaseOperations(recreateDatabase):
    print(f"\nInitiating database operations - Recreate DB: {recreateDatabase}")
    
    if recreateDatabase == 'True':
        print("Recreating database...")
        createdDbInstances = populateDB()
        print(f"Created {len(createdDbInstances)} database instances")

    if queryAttribute == "timeZoneOffset" or queryAttribute == "continent":
        print(f"Using attribute query for: {queryAttribute}")
        queryByAttribute(queryAttribute, queryRequirement)
    else:
        print("No specific query attribute, getting all cities")
        getAllCities()

print(f"\nStarting database operations with argument: {sys.argv[1]}")
initiateDatabaseOperations(sys.argv[1])
print("Database operations completed")