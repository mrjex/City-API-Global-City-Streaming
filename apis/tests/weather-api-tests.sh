# This script tests the connection to the api and the correctness of the customized configurations.
# It's value in this project can be seen in "/kafka-producer/python-producer.py", where I use the
# same weather API configurations, knowing that those calls will work, thanks to this script.



##  CONFIGURATION SECTION ##
API_KEY=165bb23217d246afb3e161429241806 # Your generated API key from your private account (https://www.weatherapi.com/my/)

# Cities to test:
declare -a CITIES=("London" "Stockholm" "Toronto" "Moscow" "Madrid" "Reykjavik" "Helsinki" "Rome", "Venice")
ATTRIBUTE_QUERY="temp_c"



##  COLOR SECTION  ##
Color_Off='\033[0m'       # Text Reset
Red='\033[0;31m'          # Red
Green='\033[0;32m'        # Green



##  MAIN SECTION  ##

i=1
for CITY in "${CITIES[@]}"
do
    # Send a request to the weather API, and check if the response JSON contains 'ATTRIBUTE_QUERY'
    if curl -X GET "https://api.weatherapi.com/v1/current.json?key=${API_KEY}&q=${CITY}&aqi=yes" | grep -q "${ATTRIBUTE_QUERY}"; then
        printf "\n\n${Green}   -------------   TEST PASSED [${CITY}]  -------------   \n\n"
        printf "        ${i}. RESPONSE ('${ATTRIBUTE_QUERY}' found)${Color_Off}\n\n\n\n"
    else
        printf "\n\n${Red}   -------------   TEST FAILED [${CITY}]   -------------   \n\n"
        printf "        ${i}. RESPONSE ('${ATTRIBUTE_QUERY}' null)${Color_Off}\n\n\n\n"
    fi

    i=$(expr $i + 1)
done