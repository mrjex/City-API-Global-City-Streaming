#####     DATABASE POSTGRES API     #####

#   - Run this script on the stored data instances in the PostgresSQL database at the same time as
#     the kafka-producer and flink-processor are doing their work and inserting new real-time
#     instances to PostgresSQL.

# This script does 3 things:
#   1) Connects to the postgres container's SQL database
#   2) Runs queries on the database
#   3) Writes the data to the corresponding city csvs in "/generated-artifacts/csvs"


# Prerequisites to running this script:
#   - All dependencies installed            (Check "/instructions-executions/executions/1. install-requirements.sh")
#   - All containers up and running         (Check "/instructions-executions/executions/2. real-time-streaming.sh")


from pandas import *
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

import psycopg2
import csv
import sys
import os
from datetime import datetime
sys.path.append('/app')
from utils import parseYmlFile


# Connect to the database (note that the container 'postgres' in docker-compose must be up and running first)
conn = psycopg2.connect(database="postgres",
                        host="postgres",
                        user="postgres",
                        password="postgres",
                        port="5432")



# Request & Response variables
cursor = conn.cursor()
res = "{}"


csvFields = ['id', 'city', 'average_temperature', 'API-Call', 'timestamp']

cities = parseYmlFile("/app/configuration.yml", "cities")

# Send a request to the database and print the response (the matched objects that qualified for the query conditions)
def queryDB(command, city):

    # Execute command and store the matching db-instances in the response variable
    cursor.execute(command)
    res = cursor.fetchall()

    # Create directories if they don't exist
    os.makedirs("/app/city-api/generated-artifacts/csvs", exist_ok=True)

    outputPath = f"/app/city-api/generated-artifacts/csvs/{city}.csv"

    # Write as a csv, the found db-instances of the current city
    with open(outputPath, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(csvFields)

        rowCount = 0 # Row 'n' represents the n:th API 'round' call

        # Iterate over response
        for dbInstance in res:
            rowCount += 1

            currentId = dbInstance[0]
            currentCity = dbInstance[1]
            currentTemperature = dbInstance[2]
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            currentRow = [[currentId, currentCity, currentTemperature, rowCount, current_timestamp]]
            csvwriter.writerows(currentRow)



def writeCityCsvs():
    for city in cities:
        queryDB(f"SELECT * FROM weather WHERE city LIKE '{city}';", city)



writeCityCsvs()