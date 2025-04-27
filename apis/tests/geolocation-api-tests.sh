#####     GEOLOCATION API TESTS     #####

# Since the api uses two public APIs, both of them are tested


NOTATION_API_URL="https://timeapi.io/api/Time/current/coordinate"   # API Website: https://timeapi.io/swagger/index.html
OFFSET_API_URL="https://api.geotimezone.com/public/timezone"        # API Website: https://www.geotimezone.com/

NOTATION_API_ATTRIBUTE_QUERY="timeZone"
OFFSET_API_ATTRIBUTE_QUERY="offset"


##  COLOR SECTION  ##
Color_Off='\033[0m'       # Text Reset
Red='\033[0;31m'          # Red
Green='\033[0;32m'        # Green



# Arguments:
#   1) The public api's url (without query parameters)
#   2) The latitude to add to the query
#   3) The longitude to add to the query
#   4) The attribute key to validate the response
#
# Function:
#   - Takes the inputted url and concatinates the query parameters. Two examples are:
#       - Notation API:
#           - Api Url (argument 1):     https://timeapi.io/api/Time/current/coordinate
#           - Query Parameters:         ?latitude=38.9&longitude=-77.03
#
#       - Offset API:                   https://api.geotimezone.com/public/timezone
#           - Api Url:                  ?latitude=-20.348404&longitude=57.552152
#
#   - Takes the response and compares it to the expected attribute key (argument 4)
#   - Prints UI to indicate what numerical tests for argument 2 and 3 passed or failed
fetchApiData() {
    LATITUDE=${2}
    LONGITUDE=${3}

    QUERY_PARAMETERS="?latitude=${LATITUDE}&longitude=${LONGITUDE}"
    API_URL="${1}${QUERY_PARAMETERS}"

    ATTRIBUTE_QUERY=${4}

    # Send a request to one of the APIs, and check if the response JSON contains 'ATTRIBUTE_QUERY'
    if curl -X GET "${API_URL}" | grep -q "${ATTRIBUTE_QUERY}"; then
        printf "\n\n${Green}   -------------   TEST PASSED [lat=${LATITUDE}, lon=${LONGITUDE}]  -------------   \n\n"
        printf "        * RESPONSE ('${ATTRIBUTE_QUERY}' found)${Color_Off}\n\n\n\n"
    else
        printf "\n\n${Red}   -------------   TEST FAILED [lat=${LATITUDE}, lon=${LONGITUDE}]   -------------   \n\n"
        printf "        * RESPONSE ('${ATTRIBUTE_QUERY}' null)${Color_Off}\n\n\n\n"
    fi
}


runNotaionApiTests() {
    fetchApiData "${NOTATION_API_URL}" 38.9 77.03 "timeZone" "${NOTATION_API_ATTRIBUTE_QUERY}"

    fetchApiData "${NOTATION_API_URL}" 33.212 47.2231 "timeZone" "${NOTATION_API_ATTRIBUTE_QUERY}"

    fetchApiData "${NOTATION_API_URL}" -12.96 -83.942 "timeZone" "${NOTATION_API_ATTRIBUTE_QUERY}"
}


runOffsetApiTests() {
    fetchApiData "${OFFSET_API_URL}" 20.348404 57.552152 "offset" "${OFFSET_API_ATTRIBUTE_QUERY}"

    fetchApiData "${OFFSET_API_URL}" 12.432 31.529 "offset" "${OFFSET_API_ATTRIBUTE_QUERY}"

    fetchApiData "${OFFSET_API_URL}" 78.224 43.868702 "offset" "${OFFSET_API_ATTRIBUTE_QUERY}"
}



###   NOTATION API TESTS   ###

runNotaionApiTests



###   OFFSET API TESTS   ###

runOffsetApiTests