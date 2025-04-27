#####     COLOR API TESTS     #####

##  DEVELOPER CONFIGURATIONS  ##
NUM_PURPLE_COLORS=18
COLOR="purple"


##  EXTERNAL CONFIGURATIONS  ##
COLOR_TEST_FILE="color-tests-${COLOR}.json"
ATTRIBUTE_QUERY="name"



##  COLOR SECTION  ##
Color_Off='\033[0m'       # Text Reset
Red='\033[0;31m'          # Red
Green='\033[0;32m'        # Green



# Function:
#   - Sends a request to the public color API and stores the json-response in the variable.
#     It proceeds with writing the fetched content to 'color-tests-purple.json' and formatting
#     or beautifying the result.
#
# Purpose:
#   - Obviously, the response from the request is fundamental for the entire application to
#     deliver an all-around quality, and therefore we need to test that it works. The more
#     interesting part is the process of storing the response as a JSON file. This was done
#     because the command in the function below (grep -c) only counts unique strings if they
#     appear on separate rows in an given file, as opposed to a variable containing one long
#     string in one row.
fetchColorData() {
    API_JSON_RESPONSE=$(curl -X GET "https://www.csscolorsapi.com/api/colors/group/${COLOR}")
    echo "${API_JSON_RESPONSE}" | python -m json.tool > "${COLOR_TEST_FILE}"
}


# Function:
#   - Checks the .json file that stores the API's response and returns the number of occurences
#     where '$ATTRIBUTE_QUERY' appears. As can be observed in 'color-tests-purple.json', a few
#     attributes in each color-object only appear once, and no where else. For instance, 'name'
#     is one of those attributes. By virtue of their occurring-patterns, we can conclude that
#     the number of times it appears is dirctly linked to the quantity of color-objects.
#
# Purpose:
#   - In the public color API, their documentation provides numerical constraints of the
#     response objects. In regards of requesting a palette of purple colors, a json-formatted
#     object of 18 objects should be returned on a successful 200-status response. This
#     function returns the number of color-objects that the API returned so that the
#     developers can confirm the correctness of the API's behavior.
#
getNumColors() {
    echo $(grep -c "${ATTRIBUTE_QUERY}" "${COLOR_TEST_FILE}")
}



fetchColorData

NUM_COLORS_FOUND=$(getNumColors)



if [ "${NUM_COLORS_FOUND}" == "${NUM_PURPLE_COLORS}" ]; then

    printf "\n\n${Green}   -------------   TEST PASSED [18 of ${NUM_PURPLE_COLORS} colors found]  -------------   \n\n"
    printf "        * RESPONSE ('${ATTRIBUTE_QUERY}', '${NUM_COLORS_FOUND}')${Color_Off}\n\n\n\n"

else

    printf "\n\n${Red}   -------------   TEST FAILED [${NUM_COLORS_FOUND} of ${NUM_PURPLE_COLORS} colors found]   -------------   \n\n"
    printf "        * RESPONSE ('${ATTRIBUTE_QUERY}','${NUM_COLORS_FOUND}')${Color_Off}\n\n\n\n"

fi
