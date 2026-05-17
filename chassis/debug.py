import pandas as pd
import re

# 1. Load the CSV exactly like the backend does
try:
    df = pd.read_csv("all_cars_datset_final.csv", on_bad_lines='skip')
    print("✅ CSV Loaded Successfully")
    print(f"Total Rows: {len(df)}")
    print(f"Columns Found: {df.columns.tolist()}")
except Exception as e:
    print(f"❌ Error Loading CSV: {e}")
    exit()

# 2. Clean Data (Mimic Backend Logic)
try:
    # Normalize headers
    df.columns = df.columns.str.strip()
    
    # Check if 'Fuel Type' exists
    if 'Fuel Type' not in df.columns:
        print("\n❌ CRITICAL: 'Fuel Type' column NOT found!")
        print("Existing columns are:", df.columns.tolist())
        exit()
    
    # Process Fuel Column
    df['hidden_fuel'] = df['Fuel Type'].astype(str).str.lower().str.strip()
    
    print("\n--- SAMPLE FUEL DATA (First 5 Rows) ---")
    print(df[['Car Name', 'Fuel Type', 'hidden_fuel']].head(5))

except Exception as e:
    print(f"❌ Error Processing Data: {e}")
    exit()

# 3. Simulate the Filter Test
print("\n--- TEST: Filtering for 'Petrol' ---")
wanted_fuel = "petrol"
# Mimic the regex pattern logic
pattern = re.escape(wanted_fuel)
filtered_df = df[df['hidden_fuel'].str.contains(pattern, case=False, regex=True)]

print(f"Looking for: '{wanted_fuel}'")
print(f"Found matches: {len(filtered_df)}")

if len(filtered_df) == 0:
    print("\n❌ DIAGNOSIS: The filter found 0 cars.")
    print("Possible Reason: The 'Fuel Type' column might be empty or formatted incorrectly.")
else:
    print("\n✅ DIAGNOSIS: Logic works! (Found cars locally)")
    print("This means the issue is likely in the Frontend (sending wrong data) or API (receiving wrong data).")