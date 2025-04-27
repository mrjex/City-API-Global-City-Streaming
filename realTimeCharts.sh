#####     REAL-TIME CHARTS     #####


# Prerequisites to executing this script:
#   - Make sure that there is a table named "weather" in the PostgresSQL database
#   - Ideally, run "/application" with docker-compose for at least 1 minute. This would generate
#     the db-instances in real-time, so that we in this script can plot the charts. Have a look
#     at the '2. real-time-streaming.sh' to complete this step.



VISUALIZE_BUBBLE_CHART="False"
VISUALIZE_PIE_CHART="False"


# Iterate over all passed arguments and check for flags.
configurePassedArgs() {
    for ARG in "$@"
    do
        if [ "${ARG}" == "-b" ]; then
            VISUALIZE_BUBBLE_CHART="True"
        elif [ "${ARG}" == "-p" ]; then
            VISUALIZE_PIE_CHART="True"
        fi
    done
}




# ./realTimeCharts.sh -b -p


# VISUALIZE_BUBBLE_CHART="True"
# VISUALIZE_PIE_CHART="True"


# If the developer wants to use the latest data when plotting the charts, then
# set this variable to true. Otherwise, use the most recent data response from
# the PostgresSQL database
RECREATE_DATABASE="False"


# Generate CSVS from the SQL database while new instances are inserted in real-time
refreshVisualizationData() {
    python3 apis/databasePostgresApi.py
}


# Plot BubbleChart & PieChart
visualizeCharts() {
    cd charts
    python main.py ${VISUALIZE_BUBBLE_CHART} ${VISUALIZE_PIE_CHART} "False"
}


configurePassedArgs "$@"


if [ "${RECREATE_DATABASE}" == "True" ]; then
    refreshVisualizationData
fi


visualizeCharts