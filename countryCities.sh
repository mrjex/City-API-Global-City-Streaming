#!/bin/bash

# Debug output redirected to stderr so it doesn't interfere with JSON output
debug() {
    echo "$1" >&2
}

debug "=== SCRIPT START ==="
debug "Testing basic output"
debug "Current directory: $(pwd)"
debug "Script arguments: $@"

# Step 1: Get the country code for the given country
COUNTRY="$1"
debug "Input country: $COUNTRY"

# Get country code from JSON file
debug "Getting country code..."
COUNTRY_CODE=$(echo "$COUNTRY" | tr '[:upper:]' '[:lower:]' | xargs | jq -r --arg country "$COUNTRY" '. | to_entries | .[] | select(.key | ascii_downcase == ($country | ascii_downcase)) | .value' /app/city-api/config/country-codes.json)
debug "Extracted country code: '$COUNTRY_CODE'"

if [ -z "$COUNTRY_CODE" ]; then
    debug "Error: Failed to get country code"
    exit 1
fi

# Get number of cities from configuration
debug "Getting number of cities from configuration..."
CITIES_LIMIT=$(yq '.services.cityApi.numberOfCitiesForSelectedCountry' /app/configuration.yml)
debug "Number of cities to fetch: $CITIES_LIMIT"

# First check if country exists in cities-data.json
debug "Checking if country exists in cities-data.json..."
CITIES_DATA=$(jq -r --arg country "$COUNTRY" '.[$country]' /app/city-api/config/cities-data.json)

if [ "$CITIES_DATA" != "null" ]; then
    debug "Found country in cities-data.json, extracting cities..."
    # Extract cities into an array
    CITIES=$(jq -r --arg limit "$CITIES_LIMIT" '.cities[0:($limit | tonumber)] | join("|")' <<< "$CITIES_DATA")
    CITY_COUNT=$(echo "$CITIES" | tr '|' '\n' | grep -v '^$' | wc -l)
    debug "Found $CITY_COUNT cities from JSON"
    
    # Get the capital city (first city in the list)
    CAPITAL_CITY=$(echo "$CITIES" | cut -d'|' -f1)
    debug "Capital city from JSON: $CAPITAL_CITY"
else
    debug "Country not found in cities-data.json, falling back to API..."
    # Store the curl response in a variable
    debug "Making API request for country code: $COUNTRY_CODE..."
    RESPONSE=$(curl -X GET "https://wft-geo-db.p.rapidapi.com/v1/geo/cities?countryIds=$COUNTRY_CODE&limit=$CITIES_LIMIT&sort=-population&types=CITY" \
      -H "X-RapidAPI-Host: wft-geo-db.p.rapidapi.com" \
      -H "X-RapidAPI-Key: $GEODB_CITIES_API_KEY")

    debug "Raw API Response:"
    debug "$RESPONSE"

    # Extract cities into an array and get count
    debug "Extracting cities..."
    CITIES=$(echo "$RESPONSE" | jq -r '.data[].city' | tr '\n' '|')
    CITY_COUNT=$(echo "$CITIES" | tr '|' '\n' | grep -v '^$' | wc -l)
    debug "Found $CITY_COUNT cities to process"

    # Get the capital city (first city in response)
    CAPITAL_CITY=$(echo "$RESPONSE" | jq -r '.data[0].city')
    debug "Capital city from API: $CAPITAL_CITY"
fi

# Get the description for this capital city from the JSON file
DESCRIPTION_KEY="$COUNTRY, $CAPITAL_CITY"
debug "Looking up description for key: $DESCRIPTION_KEY"

# First try to get description from city-edits.yml
CAPITAL_DESCRIPTION=$(yq ".countries[\"$DESCRIPTION_KEY\"].description" /app/city-api/config/city-edits.yml)
debug "Description from yml: $CAPITAL_DESCRIPTION"

# If description is null or "null", fallback to city-description.json
if [ "$CAPITAL_DESCRIPTION" = "null" ]; then
    debug "No description found in yml, falling back to city-description.json"
    CAPITAL_DESCRIPTION=$(jq -r ".[\"$DESCRIPTION_KEY\"]" /app/city-api/config/city-description.json)
fi
debug "Capital description: $CAPITAL_DESCRIPTION"

# Escape any special quotes in the description
CAPITAL_DESCRIPTION=$(echo "$CAPITAL_DESCRIPTION" | sed 's/"/\\"/g')

# First check if video exists in city-videos.json
debug "Checking if video exists in city-videos.json..."
VIDEO_DATA=$(jq -r --arg key "$DESCRIPTION_KEY" '.[$key]' /app/city-api/config/city-videos.json)

if [ "$VIDEO_DATA" != "null" ]; then
    debug "Found video in city-videos.json"
    MP4_URL=$(jq -r '.video_url' <<< "$VIDEO_DATA")
    debug "Video URL from JSON: $MP4_URL"
else
    debug "Video not found in city-videos.json, falling back to Giphy API..."
    # Get Giphy video for capital city
    GIPHY_RESPONSE=$(curl -G "https://api.giphy.com/v1/gifs/search" \
    --data-urlencode "api_key=$GIPHY_API_KEY" \
    --data-urlencode "q=$COUNTRY $CAPITAL_CITY aerial view" \
    --data-urlencode "limit=1" \
    --data-urlencode "offset=0" \
    --data-urlencode "rating=g" \
    --data-urlencode "lang=en" \
    -s)

    # Extract MP4 URL
    MP4_URL=$(echo $GIPHY_RESPONSE | jq -r '.data[0].images.original.mp4')
fi
debug "MP4 URL: $MP4_URL"

# Initialize variables for collecting city data
CITY_DATA_ARRAY=""
SEPARATOR=""
CURRENT=0

# Process cities and collect their data
debug "Starting city processing..."
OLDIFS="$IFS"
IFS='|'
for city in $CITIES; do
    if [ -n "$city" ]; then
        CURRENT=$((CURRENT + 1))
        debug "Processing city ($CURRENT/$CITY_COUNT): $city"
        # Store the city data with proper JSON formatting and ensure only JSON output is captured
        CITY_JSON=$(python /app/city-api/apis/process_cities.py "$city" 2>&2 | grep -E '^{.*}$')
        CITY_DATA_ARRAY="${CITY_DATA_ARRAY}${SEPARATOR}${CITY_JSON}"
        SEPARATOR=","
        sleep 0.1
    fi
done
IFS="$OLDIFS"

# Output the complete JSON structure
echo "{"
echo "  \"success\": true,"
echo "  \"country\": \"$COUNTRY\","
echo "  \"country_code\": \"$(echo $COUNTRY_CODE | tr '[:upper:]' '[:lower:]')\","
echo "  \"capital_city_video_link\": \"$MP4_URL\","
echo "  \"capital_city_description\": \"$CAPITAL_DESCRIPTION\","
echo "  \"cities\": ["
echo "    ${CITY_DATA_ARRAY}"
echo "  ]"
echo "}"

debug "=== SCRIPT END ==="