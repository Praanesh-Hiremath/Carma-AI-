import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import traceback
import re
import urllib.request
import xml.etree.ElementTree as ET
import csv
import os
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# --- CORS SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FILE PATH ---
# Using your exact local path
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), "cars_cleaned.csv")

# --- TAX & RTO CONFIGURATION ---
STATE_TAX_DATA = {
    "Karnataka":  {"base": 0.14, "luxury": 0.19, "ev": 0.0,  "diesel_surcharge": 0.0},
    "Delhi":      {"base": 0.07, "luxury": 0.12, "ev": 0.0,  "diesel_surcharge": 0.25},
    "Maharashtra":{"base": 0.11, "luxury": 0.13, "ev": 0.05, "diesel_surcharge": 0.02},
    "Tamil Nadu": {"base": 0.10, "luxury": 0.15, "ev": 0.05, "diesel_surcharge": 0.0},
    "Other":      {"base": 0.12, "luxury": 0.15, "ev": 0.05, "diesel_surcharge": 0.0},
}

# ─── HELPERS ────────────────────────────────────────────────────────────────

def calculate_on_road_breakdown(ex_showroom: float, fuel_type: str, state: str = "Other") -> Dict[str, str]:
    if ex_showroom == 0:
        return {"total": "Ask Dealer"}
    
    rules = STATE_TAX_DATA.get(state, STATE_TAX_DATA["Other"])
    rto_percent = rules["luxury"] if ex_showroom > 1_000_000 else rules["base"]
    fuel = fuel_type.lower()
    
    if "electric" in fuel:
        rto_percent = rules["ev"]
    elif "diesel" in fuel and rules["diesel_surcharge"] > 0:
        rto_percent += rto_percent * rules["diesel_surcharge"]
        
    rto       = ex_showroom * rto_percent
    insurance = ex_showroom * 0.035 + 5000
    tcs       = ex_showroom * 0.01 if ex_showroom > 1_000_000 else 0
    others    = 2000 + ex_showroom * 0.005
    total     = ex_showroom + rto + insurance + tcs + others

    def fmt(v):
        if v >= 10_000_000: return f"₹{v/10_000_000:.2f} Cr"
        if v >= 100_000:    return f"₹{v/100_000:.2f} Lakh"
        return f"₹{v:,.0f}"

    return {
        "ex_showroom": fmt(ex_showroom), 
        "rto": fmt(rto),
        "insurance": fmt(insurance), 
        "tcs": fmt(tcs),
        "others": fmt(others), 
        "total": fmt(total)
    }

def fetch_rss_news():
    try:
        url = "https://www.team-bhp.com/rss/news.xml"
        with urllib.request.urlopen(url, timeout=5) as r:
            root = ET.fromstring(r.read())
        items = []
        for item in root.findall('./channel/item')[:3]:
            title = item.find('title').text or "Latest Auto News"
            link  = item.find('link').text  or "#"
            desc  = item.find('description').text or ""
            items.append({
                "id": link, 
                "title": title,
                "snippet": re.sub('<[^<]+?>', '', desc)[:120] + "...",
                "image": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&q=80",
                "date": "Just Now"
            })
        return items
    except Exception as e:
        print(f"RSS Error: {e}")
        return []

# ─── LOAD DATA & BUILD SIMILARITY MATRIX ────────────────────────────────────

SIM_FEATURES = ['Price_Lakh', 'Mileage_kmpl', 'Power_BHP', 'Safety_Stars', 'Rating_is', 'Seats']

def load_data():
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        df.columns = df.columns.str.strip()
        print(f"✅ Loaded {len(df)} rows. Ready to roll.")

        df['Price_Bucket'] = pd.cut(
            df['Price_Lakh'],
            bins=[0, 10, 15, 20, 30, 50, 100, 500],
            labels=['0-10L','10-15L','15-20L','20-30L','30-50L','50-100L','100L+']
        )

        df['hidden_price']    = df['Price_Lakh'] * 100_000
        df['hidden_fuel']     = df['Fuel Type'].astype(str).str.lower().str.strip()
        df['hidden_body_type']= df['Body Type'].astype(str).str.lower().str.strip()
        df['hidden_seats']    = pd.to_numeric(df['Seats'], errors='coerce').fillna(5).astype(int)

        return df
    except Exception as e:
        print(f"❌ Load error: {e}")
        return pd.DataFrame()

def build_similarity_matrix(df: pd.DataFrame):
    try:
        sub = df[SIM_FEATURES].copy().fillna(df[SIM_FEATURES].median())
        body_dummies = pd.get_dummies(df['Body Type'], prefix='Body')
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(sub)
        scaled_df = pd.DataFrame(scaled, columns=SIM_FEATURES, index=df.index)
        
        # Weight adjustments: Price is 2x, Body Type is 3x
        scaled_df[SIM_FEATURES] = scaled_df[SIM_FEATURES] * [2,1,1,1,1,1]
        combined = pd.concat([scaled_df, body_dummies * 3], axis=1)
        
        matrix = cosine_similarity(combined)
        print("✅ Cosine Similarity matrix built successfully.")
        return matrix, scaler
    except Exception as e:
        print(f"❌ Similarity matrix error: {e}")
        return None, None

car_data                    = load_data()
similarity_matrix, _scaler  = build_similarity_matrix(car_data)

# ─── API MODELS ──────────────────────────────────────────────────────────────

class UserPreferences(BaseModel):
    budget: float
    seating_capacity: int
    priorities: List[str] = []
    fuel_types: List[str] = []
    body_types: List[str] = []
    specific_needs: str = ""
    search_query: str = ""
    state: str = "Other"

class LeadRequest(BaseModel):
    name: str
    phone: str
    city: str
    car_model: str

# ─── ENDPOINTS ───────────────────────────────────────────────────────────────

@app.get("/news")
async def get_news():
    return fetch_rss_news()

@app.post("/submit-lead")
async def submit_lead(lead: LeadRequest):
    try:
        exists = os.path.isfile("leads.csv")
        with open("leads.csv", "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if not exists:
                w.writerow(["Timestamp","Name","Phone","City","Car"])
            w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        lead.name, lead.phone, lead.city, lead.car_model])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend")
async def get_recommendations(prefs: UserPreferences):
    try:
        if car_data.empty:
            raise Exception("Dataset is empty. Check CSV path.")

        df = car_data.copy()

        # ── 1. HERO SEARCH ───────────────────────────────────────────────────
        if prefs.search_query:
            q = prefs.search_query.lower().strip()
            mask = (
                df['Car Name'].str.lower().str.contains(q, regex=False) |
                df['Brand'].str.lower().str.contains(q, regex=False) |
                df['hidden_body_type'].str.contains(q, regex=False)
            )
            df = df[mask]

        else:
            # ── 2. HARD FILTERS ───────────────────────────────────────────────
            df = df[df['hidden_price'] <= prefs.budget * 1.1]

            if prefs.seating_capacity >= 7:
                df = df[df['hidden_seats'] >= 7]
            elif prefs.seating_capacity == 2:
                df = df[df['hidden_seats'] <= 4]
            else:
                df = df[df['hidden_seats'] >= 5]

            if prefs.fuel_types:
                pattern = "|".join(re.escape(f.lower()) for f in prefs.fuel_types)
                df = df[df['hidden_fuel'].str.contains(pattern, case=False, regex=True)]

            if prefs.body_types:
                pattern = "|".join(re.escape(b.lower()) for b in prefs.body_types)
                df = df[df['hidden_body_type'].str.contains(pattern, case=False, regex=True)]

        if df.empty:
            return []

        # ── 3. COSINE SIMILARITY SCORING ─────────────────────────────────────
        filtered_indices = df.index.tolist()

        if similarity_matrix is not None and len(filtered_indices) > 1:
            sub_matrix = similarity_matrix[np.ix_(filtered_indices, filtered_indices)]
            np.fill_diagonal(sub_matrix, 0)
            mean_sim = sub_matrix.mean(axis=1) 
            if mean_sim.max() > mean_sim.min():
                normalized = 60 + ((mean_sim - mean_sim.min()) /
                                   (mean_sim.max() - mean_sim.min())) * 35
            else:
                normalized = np.full(len(mean_sim), 75.0)
        else:
            normalized = np.full(len(filtered_indices), 75.0)

        # ── 4. SMART KEYWORD MATCHING (Zero-Latency Vibe Check) ──────────────
        keywords = []
        if prefs.specific_needs:
            # Extract words longer than 3 characters (ignores "and", "the", etc.)
            keywords = [w.lower() for w in re.findall(r'\b\w+\b', prefs.specific_needs) if len(w) > 3]

        results = []
        for i, (idx, row) in enumerate(df.iterrows()):
            score    = float(normalized[i])
            ai_notes = []
            cons     = []

            body_lower = str(row.get('Body Type','')).lower()
            fuel_lower = str(row.get('Fuel Type','')).lower()

            # Keyword Boost
            if keywords:
                matched = []
                # Search across name, brand, body, and hidden features
                search_text = f"{row.get('Car Name','')} {row.get('Brand','')} {body_lower} {str(row.get('Features',''))}".lower()
                for kw in keywords:
                    if kw in search_text:
                        score = min(99, score + 4)
                        matched.append(kw)
                if matched:
                    # Keep the frontend happy with the "sparkles" UI
                    ai_notes.append(f"✨ Matches your request: {', '.join(set(matched))}")

            # Priority boosts
            if "Mileage" in prefs.priorities and row.get('Mileage_kmpl', 0) > 18:
                score = min(99, score + 5)
            if "Safety" in prefs.priorities and row.get('Safety_Stars', 0) >= 4:
                score = min(99, score + 5)

            # Cons Logic
            mileage = row.get('Mileage_kmpl', 0)
            if pd.notna(mileage) and 0 < mileage < 12:
                cons.append("Low Mileage")

            # On-road price
            ex_showroom   = row.get('hidden_price', 0)
            price_breakdown = calculate_on_road_breakdown(ex_showroom, fuel_lower, prefs.state)

            # --- SMART IMAGE LOGIC ---
            img_val = row.get('image_url')
            if pd.notna(img_val) and str(img_val).strip() not in ["", "None", "nan"] and str(img_val).startswith("http"):
                final_image = str(img_val).strip()
            else:
                # Fallback to Unsplash if Wikipedia failed for this specific car
                final_image = (
                    "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&q=80"
                    if "suv" in body_lower else
                    "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&q=80"
                )

            results.append({
                "match_score": round(score),
                "car_details": {
                    "make":             row.get('Brand', 'Unknown'),
                    "model":            row.get('Car Name', 'Unknown'),
                    "image":            final_image,
                    "ex_showroom_price": f"₹{row.get('Price_Lakh','N/A')} Lakh",
                    "on_road_price":    price_breakdown,
                    "mileage":          f"{row.get('Mileage_kmpl','N/A')} kmpl",
                    "safety_rating":    f"{row.get('Safety_Stars','N/A')}★",
                    "horsepower":       f"{row.get('Power_BHP','N/A')} bhp",
                    "fuel_type":        row.get('Fuel Type','N/A'),
                    "body_type":        row.get('Body Type','N/A'),
                    "features":         [],
                },
                "ai_notes": ai_notes,
                "cons":     cons,
            })

        # Sort by best match
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:20]

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")