###   TIME ZONE API   ###

# This script uses 2 different APIs, both of which are dependent on user-inputted
# geo-coordinates. This script serves as the composer of these two in Python-form
# that the fetched responses to the other components of this system upon request

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)

apiNotationUrl = "https://timeapi.io/api/Time/current/coordinate"     # API Website: https://timeapi.io/swagger/index.html
apiOffsetUrl = "https://api.geotimezone.com/public/timezone"          # API Website: https://www.geotimezone.com/


# NOTES:

# Returns a notation-string about the timezone that's easy for humans to read.
# Examples: 'Europe/Amsterdam', 'Europe/Paris', 'Africa/Nairobi', 'Asia/Dubai'

# Returns a string that makes it easy to distinguish between
# the cities' timezone differentes.
# Examples: 'UTC+0', 'UTC+9', 'UTC+2', 'UTC-6'

def fetchApiData(apiUrl, latitude, longitude, attributeKey):
    query = {'latitude': latitude, 'longitude': longitude}
    try:
        # First try with SSL verification
        response = session.get(apiUrl, params=query)
        response.raise_for_status()
    except requests.exceptions.SSLError:
        # If SSL fails, try without verification
        print(f"Warning: SSL verification failed for {apiUrl}, retrying without verification")
        response = session.get(apiUrl, params=query, verify=False)
        response.raise_for_status()
    
    body_dict = response.json()
    return body_dict[attributeKey]



# Returns a key-value structure such that the values represent the city's timezone's
# human-readable notation as well as its hourly offset from the standard UTC time
def fetchTimeZoneData(latitude, longitude):

  return {
        'timeZoneNotation': fetchApiData(apiNotationUrl, latitude, longitude, "timeZone"),
        'timeZoneOffset': fetchApiData(apiOffsetUrl, latitude, longitude, "offset")
     }