import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import traceback
import re
import random
import datetime

app = FastAPI()

# --- CORS SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_FILE_PATH = "C:\Users\Praanesh\OneDrive\Desktop\=Praan=\codes\CarRecommendation\google version\backend-google\cars_cleaned.csv"

# --- 1. INTELLIGENCE LAYERS ---
FEATURE_TRANSLATION = {
    "back pain": "lumbar support", "bad back": "lumbar support",
    "kids": "isofix", "child": "isofix", "baby": "isofix",
    "pollution": "air purifier", "dust": "air purifier",
    "music": "premium audio", "sound": "premium audio", "bass": "premium audio",
    "sun": "sunroof", "view": "panoramic sunroof", "sky": "sunroof",
    "hot": "ventilated seats", "summer": "ventilated seats", "sweat": "ventilated seats",
    "highway": "cruise control", "lazy": "adas", "safe": "adas",
    "charging": "wireless charger", "phone": "wireless charger",
    "luxury": "ambient lighting", "parking": "360 camera",
    "tight spots": "360 camera", "off road": "4x4", "mud": "4x4",
    "hills": "hill hold control", "slope": "hill hold control"
}

CONCEPT_MAP = {
    "macho": {
        "keywords": ["macho", "road presence", "beast", "muscle", "rugged", "aggressive", "bulky", "gangster", "don"],
        "target_models": ["thar", "scorpio", "fortuner", "defender", "g-class", "gloster", "hilux", "wrangler", "gurkha", "endeavour", "jimny"],
        "target_body_types": ["suv", "pickup"],
        "boost_score": 40
    },
    "luxury_vip": {
        "keywords": ["ceo", "boss", "vip", "luxury", "chauffeur", "status", "quiet", "business", "rich"],
        "target_models": ["s-class", "7 series", "a8", "vellfire", "camry", "lexus", "maybach", "phantom", "ghost"],
        "target_body_types": ["sedan", "mpv"],
        "boost_score": 30
    },
    "city_zippy": {
        "keywords": ["traffic", "parking", "small", "cute", "zippy", "easy", "beginner", "college"],
        "target_models": ["swift", "ignis", "tiago", "i10", "comet", "alto", "celerio", "baleno", "wagon r"],
        "target_body_types": ["hatchback"],
        "boost_score": 25
    },
    "performance": {
        "keywords": ["fast", "race", "speed", "drift", "fun", "enthusiast", "0-100", "sport"],
        "target_models": ["m340i", "m4", "m5", "porsche", "ferrari", "lamborghini", "amg", "rs5", "n line", "gt"],
        "target_body_types": ["coupe", "sedan"],
        "boost_score": 35
    }
}

# --- 2. HELPER FUNCTIONS ---
def clean_indian_price(value):
    s = str(value).lower().strip()
    numbers = re.findall(r"\d+(?:\.\d+)?", s)
    if not numbers: return 0.0
    try: base_price = float(numbers[0])
    except: return 0.0
    
    if 'cr' in s or 'crore' in s: return base_price * 10000000
    elif 'lakh' in s or 'lac' in s: return base_price * 100000
    else: return base_price * 100000 if base_price < 500 else base_price

def calculate_on_road_breakdown(ex_showroom: float, fuel_type: str) -> Dict[str, str]:
    """
    Estimates On-Road Price for India (Generic Average).
    RTO: High for Diesel/Petrol, Low/Zero for Electric.
    Insurance: ~3-4% of value.
    """
    if ex_showroom == 0:
        return {"total": "Ask Dealer"}

    # 1. RTO Logic (Registration Tax)
    rto_percent = 0.12 # Base 12%
    if "electric" in fuel_type.lower():
        rto_percent = 0.01 # EV Subsidy (approx)
    elif "diesel" in fuel_type.lower():
        rto_percent = 0.15 # Higher tax for diesel
    elif ex_showroom > 2000000:
        rto_percent += 0.05 # Luxury tax tier

    rto_cost = ex_showroom * rto_percent

    # 2. Insurance Logic (Approx 3.5% + 3rd Party)
    insurance_cost = (ex_showroom * 0.035) + 5000 

    # 3. Other Charges (FastTag, Handling, Basic Accessories)
    other_charges = 2000 + (ex_showroom * 0.005)

    total_on_road = ex_showroom + rto_cost + insurance_cost + other_charges

    # Format helpers
    def fmt(val):
        if val >= 10000000: return f"₹{val/10000000:.2f} Cr"
        if val >= 100000: return f"₹{val/100000:.2f} Lakh"
        return f"₹{val:,.0f}"

    return {
        "ex_showroom": fmt(ex_showroom),
        "rto": fmt(rto_cost),
        "insurance": fmt(insurance_cost),
        "others": fmt(other_charges),
        "total": fmt(total_on_road)
    }

def clean_seats(value):
    s = str(value).lower().strip()
    numbers = re.findall(r"\d+", s)
    if not numbers: return 5 
    return max([int(n) for n in numbers])

def parse_mileage(value):
    s = str(value).lower().strip()
    numbers = re.findall(r"\d+(?:\.\d+)?", s)
    if not numbers: return 0.0
    val = max([float(n) for n in numbers])
    if 'kmpl' in s: return val
    return 0.0

def parse_ev_range(value):
    s = str(value).lower().strip()
    numbers = re.findall(r"\d+(?:\.\d+)?", s)
    if not numbers: return 0.0
    val = max([float(n) for n in numbers])
    if 'km' in s and 'kmpl' not in s: return val
    if val > 100 and 'kmpl' not in s: return val
    return 0.0

# --- 3. LOAD DATA ---
def load_data():
    try:
        df = pd.read_csv(CSV_FILE_PATH, on_bad_lines='skip')
        print(f"\n✅ CSV Loaded. Found {len(df)} rows.")
        
        if 'Price' in df.columns:
            df['hidden_price'] = df['Price'].apply(clean_indian_price)
        else: df['hidden_price'] = 0.0

        seat_col = 'Seats' if 'Seats' in df.columns else ('Seating Capacity' if 'Seating Capacity' in df.columns else None)
        if seat_col: df['hidden_seats'] = df[seat_col].apply(clean_seats)
        else: df['hidden_seats'] = 5

        mil_col = 'Mileage' if 'Mileage' in df.columns else ('Mileage/Range' if 'Mileage/Range' in df.columns else None)
        df.attrs['mil_col_name'] = mil_col 
        if mil_col:
            df['hidden_ice_efficiency'] = df[mil_col].apply(parse_mileage)
            df['hidden_ev_range'] = df[mil_col].apply(parse_ev_range)
        else:
            df['hidden_ice_efficiency'] = 0.0
            df['hidden_ev_range'] = 0.0

        if 'Power (BHP)' in df.columns:
            df['hidden_power'] = df['Power (BHP)'].apply(lambda x: max([float(n) for n in re.findall(r"\d+(?:\.\d+)?", str(x))] or [0.0]))
        else: df['hidden_power'] = 0.0

        if 'Features' in df.columns:
            df['hidden_features'] = df['Features'].astype(str).apply(lambda x: [f.strip().lower() for f in x.split(',') if f.strip().lower() != 'nan'])
        else: df['hidden_features'] = [[] for _ in range(len(df))]
            
        if 'Fuel Type' in df.columns:
            df['hidden_fuel'] = df['Fuel Type'].astype(str).str.lower().str.strip()
        else: df['hidden_fuel'] = "petrol"

        if 'Body Type' in df.columns:
            df['hidden_body_type'] = df['Body Type'].astype(str).str.lower().str.strip()
        else: df['hidden_body_type'] = "suv"

        return df.fillna("N/A") 
    except Exception as e:
        print(f"❌ CRITICAL ERROR LOADING CSV: {e}")
        traceback.print_exc()
        return pd.DataFrame() 

car_data = load_data()

class UserPreferences(BaseModel):
    budget: float
    seating_capacity: int
    priorities: List[str] = []
    fuel_types: List[str] = []
    body_types: List[str] = []
    specific_needs: str = ""

@app.get("/news")
async def get_news():
    # Mock News Data (In real world, scrape this or use an API)
    return [
        {
            "id": 1,
            "title": "Mahindra Thar Roxx Waitlist hits 12 Months",
            "snippet": "The new 5-door Thar has seen unprecedented demand, pushing delivery timelines into late 2025.",
            "image": "https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?auto=format&fit=crop&q=80",
            "date": "Today"
        },
        {
            "id": 2,
            "title": "Tesla India Launch Confirmed for Q4",
            "snippet": "Government policies on EV import taxes have finally paved the way for the Model 3 entry.",
            "image": "https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&q=80",
            "date": "Yesterday"
        },
        {
            "id": 3,
            "title": "Tata Curvv EV vs Hyundai Creta EV",
            "snippet": "A detailed comparison of the upcoming mid-size electric SUV battle in India.",
            "image": "https://images.unsplash.com/photo-1593055424755-d990432360b5?auto=format&fit=crop&q=80",
            "date": "2 days ago"
        }
    ]

@app.post("/recommend")
async def get_recommendations(prefs: UserPreferences):
    try:
        if car_data.empty: raise Exception("CSV is empty.")
        
        filtered = car_data[car_data['hidden_price'] <= (prefs.budget * 1.1)].copy()

        if prefs.fuel_types:
            wanted_fuels = [f.lower() for f in prefs.fuel_types]
            filtered = filtered[filtered['hidden_fuel'].isin(wanted_fuels)]

        if prefs.body_types:
            wanted_bodies = [b.lower() for b in prefs.body_types]
            filtered = filtered[filtered['hidden_body_type'].isin(wanted_bodies)]

        if prefs.seating_capacity == 2:
            def is_coupe_match(row):
                seats = row['hidden_seats']
                body = str(row.get('Body Type', '')).lower()
                if seats == 2: return True
                if seats == 4 and any(x in body for x in ['coupe', 'convertible', 'roadster']): return True
                return False
            filtered = filtered[filtered.apply(is_coupe_match, axis=1)]
        elif prefs.seating_capacity >= 7:
            filtered = filtered[filtered['hidden_seats'] >= 7]
        else:
            filtered = filtered[filtered['hidden_seats'] >= 5]

        # --- AI & VIBE CHECK ---
        user_input_lower = prefs.specific_needs.lower()
        active_concepts = []
        for concept_key, concept_data in CONCEPT_MAP.items():
            if any(k in user_input_lower for k in concept_data["keywords"]):
                active_concepts.append(concept_data)

        translated_needs = []
        raw_needs_list = [n.strip() for n in user_input_lower.split(',') if n.strip()]
        for need in raw_needs_list:
            translated = need 
            for key, val in FEATURE_TRANSLATION.items():
                if key in need:
                    translated = val
                    break
            translated_needs.append(translated)

        results = []
        is_luxury_search = prefs.budget > 5000000

        for index, row in filtered.iterrows():
            score = 75 
            ai_notes = []
            cons = [] 
            
            car_name_lower = str(row.get('Car Name', '')).lower()
            brand_lower = str(row.get('Brand', '')).lower()
            body_type_lower = str(row.get('Body Type', '')).lower()
            fuel_type_lower = str(row.get('Fuel Type', '')).lower()
            car_features = [body_type_lower] + row['hidden_features']

            # Scoring Logic
            for concept in active_concepts:
                if any(model in car_name_lower for model in concept["target_models"]):
                    score += concept["boost_score"]
                    ai_notes.append(f"🔥 Matches your '{concept['keywords'][0]}' vibe perfectly.")
                elif any(bt in body_type_lower for bt in concept["target_body_types"]):
                    score += 10 

            if "Mileage" in prefs.priorities:
                if row['hidden_ice_efficiency'] > 18: score += 10
                elif row['hidden_ev_range'] > 350: score += 10
            
            if "Safety" in prefs.priorities:
                try:
                    rating = float(str(row.get('Safety', '0')).replace('★', '').replace('Star', '').strip())
                    if rating >= 4: score += 10
                except: pass

            if "Power" in prefs.priorities:
                threshold = 200 if is_luxury_search else 100
                if row['hidden_power'] > threshold: score += 10
            
            if "Rough Roads" in prefs.priorities:
                if any(x in body_type_lower for x in ['suv', 'muv']): score += 10
            
            matched_features = []
            for tech_term in translated_needs:
                if any(tech_term in f for f in car_features):
                    score += 15
                    matched_features.append(tech_term)
            if matched_features:
                ai_notes.append(f"✅ Has {', '.join(list(set(matched_features)))}")

            # Cons Logic
            if any(b in brand_lower for b in ['tata', 'citroen', 'jeep']):
                cons.append("Service inconsistent in some areas.")
            if not is_luxury_search and 0 < row['hidden_ice_efficiency'] < 12:
                cons.append("Low Mileage (<12 kmpl).")
            if row['hidden_ev_range'] > 0 and row['hidden_ev_range'] < 250:
                cons.append("Limited Range (City only).")

            # On-Road Price Calculation
            price_breakdown = calculate_on_road_breakdown(row['hidden_price'], fuel_type_lower)

            mil_disp = row.get(car_data.attrs.get('mil_col_name', 'Mileage'), 'N/A')
            
            results.append({
                "match_score": min(99, score),
                "car_details": {
                    "make": row.get('Brand', 'Unknown'),
                    "model": row.get('Car Name', 'Unknown'),
                    "image": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&q=80" if "suv" in body_type_lower 
                             else "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&q=80" if "coupe" in body_type_lower
                             else "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&q=80",
                    "ex_showroom_price": row.get('Price', 'Ask Dealer'),
                    "on_road_price": price_breakdown, # New Field
                    "mileage": mil_disp, 
                    "safety_rating": row.get('Safety', 'N/A'),
                    "horsepower": f"{row.get('Power (BHP)', 'N/A')}",
                    "fuel_type": row.get('Fuel Type', 'N/A'),
                    "body_type": row.get('Body Type', 'N/A'),
                    "features": car_features 
                },
                "ai_notes": ai_notes,
                "cons": cons 
            })

        results = sorted(results, key=lambda x: x['match_score'], reverse=True)
        return results[:20]

    except Exception as e:
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")