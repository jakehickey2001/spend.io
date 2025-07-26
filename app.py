import streamlit as st
import os
import pandas as pd
import openai

# === OPENAI SETUP ===
openai.api_key = os.getenv("OPENAI_API_KEY")

# === CLEAN DESCRIPTION ===
def clean_description(desc):
    desc = str(desc).lower()
    for junk in ["vdp-", "vdc-", "vdcs-", "vdd-", "*", "-", ".", ","]:
        desc = desc.replace(junk, "")
    return desc.strip()

# === GPT CATEGORY FUNCTION WITH CACHING ===
@st.cache_data(show_spinner=False)
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
        # Optional: log token usage
        print("Tokens used:", response["usage"]["total_tokens"])
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("GPT Error:", e)
        return "Other"

# === STREAMLIT APP ===
st.title("💸 Smart Transaction Categorizer (GPT-only)")
st.write("Upload a bank CSV and let GPT categorize each transaction.")

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
            category = gpt_category(desc)
            categories.append(category)
            progress.progress((i + 1) / total)
            status_text.text(f"{i + 1} of {total} transactions done")

        df["Category"] = categories
        st.success("🎉 Done! Here's the result:")
        st.dataframe(df[[desc_col, "Category"]])

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Categorized CSV", csv, "categorized_transactions.csv", "text/csv")
