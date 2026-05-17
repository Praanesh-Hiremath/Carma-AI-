import pandas as pd

try:
    # 'on_bad_lines' tells pandas to skip rows with errors instead of crashing
    df = pd.read_csv("all_cars_datset_final.csv", on_bad_lines='skip')
    print("\n--- YOUR CSV COLUMNS ARE: ---")
    print(df.columns.tolist())
    print("-----------------------------\n")
    print("⚠️  NOTE: We skipped some bad rows (like line 21) to show you this list.")
except Exception as e:
    print("Could not read file:", e)