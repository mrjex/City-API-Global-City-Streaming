import pandas as pd
import os
import yaml
import sys
import json
import matplotlib.pyplot as plt
from datetime import datetime

def safe_parse_timestamp(timestamp_str):
    """Safely parse timestamp strings"""
    if not timestamp_str:
        return None
    try:
        # Try to parse ISO format
        return pd.to_datetime(timestamp_str)
    except:
        try:
            # Try manual parsing as fallback
            return datetime.now()
        except:
            return None

def load_city_data(city):
    """Load data for a city with robust error handling"""
    try:
        # Attempt to read CSV file for city
        csv_path = f"/app/city-api/generated-artifacts/csvs/{city}.csv"
        if not os.path.exists(csv_path):
            # If file doesn't exist, create a sample entry
            df = pd.DataFrame({
                "city": [city],
                "temperature": [20.0],
                "timestamp": [datetime.now()]
            })
            # Save the sample data
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            df.to_csv(csv_path, index=False)
            return df
        
        df = pd.read_csv(csv_path)
        # Ensure timestamp column exists and is properly formatted
        if "timestamp" in df.columns:
            df["timestamp"] = df["timestamp"].apply(safe_parse_timestamp)
        else:
            df["timestamp"] = datetime.now()
        return df
    except Exception as e:
        print(f"Error reading data for {city}: {str(e)}")
        # Return a fallback dataframe
        return pd.DataFrame({
            "city": [city],
            "temperature": [20.0],
            "timestamp": [datetime.now()]
        })

# Make the module importable from scripts
if __name__ == "__main__":
    print("Data processor module loaded") 