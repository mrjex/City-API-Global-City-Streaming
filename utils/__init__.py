# Initialize utils package
import yaml
import os


# Function:
#   - This function parses a key-value structured file, by traversing the nested
#     structure separated by dots. With that said, it allows you to access values
#     of the desired attributes
#
# Parameters:
#   - pathToConfigFile: The local path to 'configuration.yml' from the python file
#                       in which the function was invoked from
#
#   - commands: A string seperated by '.' such that each substring is a new nested
#               branch in the .yml file. Note that if the provided string is incomplete
#               i.e it doesn't end in the deepest key-value pair, then a nested
#               key-value structure is returned. A few appropriate values for this
#               parameter, with respect to the already existing 'configuration.yml'
#               file, are:
#                   - "debugApi.queryConfig.queryAttribute"
#                   - "debugApi.queryConfig.queryRequirement"
#                   - "debugApi.charts.bubbleChart.bubbleColorTheme"
#                   - "debugApi.charts.equatorChart.displayLogarithmicTrend"
#

def parseYmlFile(file_path, dot_path):
    try:
        if not os.path.exists(file_path):
            print(f"Warning: YAML file not found at: {file_path}")
            return None
            
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Split the path and traverse the nested dictionaries
        path_parts = dot_path.split('.')
        current = data
        
        for part in path_parts:
            if not isinstance(current, dict) or part not in current:
                # Handle path parts that don't exist
                print(f"Warning: Path '{dot_path}' not found in YAML file. Failed at '{part}'")
                return None
            current = current[part]
        
        return current
    except Exception as e:
        print(f"Error parsing YAML file {file_path} with path {dot_path}: {str(e)}")
        return None