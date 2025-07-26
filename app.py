import streamlit as st
import os
import pandas as pd
import openai
import googlemaps

# === YOUR API KEYS ===
openai.api_key = os.getenv("OPENAI_API_KEY")
gmaps = googlemaps.Client(key="AIzaSyBhJaWSK_aXvAEk1xjLdEmnXgRD2F_uYvY")

# === HARD-CODED MATCHES ===
keyword_rules = {
    "aldi": "Groceries",
    "centra": "Groceries",
    "lidl": "Groceries",
    "tesco": "Groceries",
    "ryanair": "Transport",
    "revolut": "Transfers",
    "uber": "Transport",
    "omniplex": "Entertainment",
    "cinema": "Entertainment",
    "audible": "Entertainment",
    "kebab": "Food & Dining",
    "cafe": "Cafe",
    "pub": "Drinking",
    "bar": "Drinking",
    "pharmacy": "Health",
    "boots": "Health",
    "hotel": "Lodging",
    "airbnb": "Lodging",
    "amazon": "Shopping",
    "zara": "Shopping",
}

# === CLEAN DESCRIPTION ===
def clean_description(desc):
    desc = str(desc).lower()
    for junk in ["vdp-", "vdc-", "vdcs-", "vdd-", "*", "-", ".", ","]:
        desc = desc.replace(junk, "")
    return desc.strip()

# === MATCHING FUNCTIONS ===
def keyword_category(desc):
    for word, category in keyword_rules.items():
        if word in desc:
            return category
    return None

def google_places_category(desc):
    try:
        result = gmaps.places(desc + " ireland")
        if result["status"] == "OK" and result["results"]:
            types = result["results"][0]["types"]
            if any(x in types for x in ["bar", "night_club", "liquor_store"]):
                return "Drinking"
            if any(x in types for x in ["restaurant", "meal_takeaway", "food"]):
                return "Food & Dining"
            if any(x in types for x in ["cafe", "bakery"]):
                return "Cafe"
            if any(x in types for x in ["pharmacy", "health"]):
                return "Health"
            if any(x in types for x in ["supermarket", "convenience_store", "grocery_or_supermarket"]):
                return "Groceries"
            if any(x in types for x in ["movie_theater", "amusement_park"]):
                return "Entertainment"
            if any(x in types for x in ["clothing_store", "shopping_mall"]):
                return "Shopping"
            if any(x in types for x in ["lodging", "hotel"]):
                return "Lodging"
            if any(x in types for x in ["taxi_stand", "bus_station", "airport", "subway_station", "train_station"]):
                return "Transport"
        return None
    except Exception:
        return None

def gpt_category(desc):
    try:
        prompt = (
            f"This is a transaction from a bank: '{desc}'. "
            "What type of business is this likely to be? Pick ONE category from this list: "
            "Drinking, Groceries, Transport, Shopping, Health, Cafe, Food & Dining, Lodging, Transfers, Entertainment, Other. "
            "Only reply with the category name."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception:
        return "Other"

# === STREAMLIT APP ===
st.title("💸 Smart Transaction Categorizer (with Progress Bar)")
st.write("Upload a bank CSV and let the app figure out what each transaction is.")

uploaded_file = st.file_uploader("📂 Upload your CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("✅ Here's a preview of your data:")
    st.dataframe(df.head())

    desc_col = st.selectbox("👉 Select the column with transaction descriptions:", df.columns)

    if st.button("🚀 Categorize Transactions"):
        st.write("Thinking hard... 🧠 This may take a few minutes.")

        df["Cleaned_Description"] = df[desc_col].apply(clean_description)
        categories = []
        total = len(df)
        progress = st.progress(0)
        status_text = st.empty()

        for i, desc in enumerate(df["Cleaned_Description"]):
            category = keyword_category(desc)
            if not category:
                category = google_places_category(desc)
            if not category:
                category = gpt_category(desc)

            categories.append(category)
            progress.progress((i + 1) / total)
            status_text.text(f"{i + 1} of {total} transactions done")

        df["Category"] = categories
        st.success("🎉 Done! Here's the result:")
        st.dataframe(df[[desc_col, "Category"]])

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Categorized CSV", csv, "categorized_transactions.csv", "text/csv")
