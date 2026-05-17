import pandas as pd
import os

# Define the CSV path clearly
CSV_PATH = "all_cars_datset_final.csv"

def load_car_data():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found!")
        return pd.DataFrame() # Return empty if missing

    try:
        df = pd.read_csv(CSV_PATH)
        
        # --- Data Cleaning ---
        # 1. Standardize Column Names (strip spaces)
        df.columns = [c.strip() for c in df.columns]

        # 2. Clean Price Column (Remove symbols like $, ₹, commas)
        # We look for a column with 'price' in the name
        price_col = next((c for c in df.columns if 'price' in c.lower()), None)
        if price_col:
            df[price_col] = df[price_col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df[price_col] = pd.to_numeric(df[price_col], errors='coerce').fillna(0)

        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()

def get_unique_body_types():
    df = load_car_data()
    # Look for 'Body Type', 'Class', or 'Type' column
    body_col = next((c for c in df.columns if c.lower() in ['body type', 'body_type', 'type', 'class']), None)
    
    if body_col and not df.empty:
        # Get unique values, remove NaNs, sort them
        return sorted(df[body_col].dropna().unique().tolist())
    return []

def filter_cars(body_type=None):
    df = load_car_data()
    
    if df.empty:
        return []

    # Filter by Body Type if provided
    if body_type and body_type != "All":
        body_col = next((c for c in df.columns if c.lower() in ['body type', 'body_type', 'type', 'class']), None)
        if body_col:
            df = df[df[body_col] == body_type]

    # Convert to dictionary for JSON response
    return df.to_dict(orient="records")