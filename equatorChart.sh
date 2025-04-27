#!/bin/bash

echo "Starting equator chart script..."
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Python path: $(which python)"

#####     EQUATOR CHART     #####


# STEPS FOR DEVELOPER:

#   1. Change configurations in 'configuration.yml'
#   2. Run this script, which does 2 things:
#       - 1) Runs a the specified query from the .yml file on the "/apis/database/db.json" file
#       - 2) Visualizes the cities and their data on a plot



VISUALIZE_EQUATOR_CHART="True"



# Setting this variable to true implies that the db.json file will be overwritten by the new
# cities. As long as you only want to query the data on already-existing cities you can leave
# this as 'False'. On the contrary, if you wish to add/remove cities in the database (i.e you
# have modified the 'citiesPool' list in 'configuration-yml'), then you may set this variable
# to 'True'. Note that enabling this will cause a longer response delay, since all defined cities will
# go through a process of retrieval of each of their JSON city-object values. For instance,
# the attribute 'temperatureCelsius' is fetched from "/apis/weatherApi.py" and 'timeZoneOffset'
# is fetched from "/apis/timezoneApi.py".

RECREATE_DATABASE="False"

echo "Step 1 - Query DB"
cd /app/city-api/apis

echo "Running databaseJsonApi.py..."
python /app/city-api/apis/databaseJsonApi.py ${RECREATE_DATABASE}

echo "Step 2 - Visualize data"
cd /app/city-api/charts

echo "Running main.py..."
# Capture and forward the output from main.py
python /app/city-api/charts/main.py "False" "False" ${VISUALIZE_EQUATOR_CHART}