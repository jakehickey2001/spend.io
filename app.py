import streamlit as st
import os
import pandas as pd
import openai

# === YOUR API KEY ===
openai.api_key = os.getenv("OPENAI_API_KEY")

# === CLEAN DESCRIPTION ===
def clean_description(desc):
    desc = str(desc).lower()
    for junk in ["vdp-", "vdc-", "vdcs-", "vdd-", "*", "-", ".", ","]:
        desc = desc.replace(junk, "")
    return desc.strip()

# === GPT CATEGORY FUNCTION ===
def gpt_category(desc, index):
    prompt = (
        f"This is a transaction from a bank: '{desc}'. "
        "What type of business is this likely to be? Pick ONE category from this list: "
        "Drinking, Groceries, Transport, Shopping, Health, Cafe, Food & Dining, Lodging, Transfers, Entertainment, Other. "
        "Only reply with the category name."
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        category = response.choices[0].message.content.strip()
    except Exception as e:
        category = "Other"
        st.error(f"Error processing transaction {index + 1}: {e}")

    st.text_area(f"Prompt {index + 1}", prompt, height=100)
    st.text_area(f"Response {index + 1}", category, height=80)

    return category

# === STREAMLIT APP ===
st.title("💸 Smart Transaction Categorizer (OpenAI Only)")
st.write("Upload a bank CSV and let the app categorize each transaction using OpenAI GPT.")

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
            category = gpt_category(desc, i)
            categories.append(category)
            progress.progress((i + 1) / total)
            status_text.text(f"{i + 1} of {total} transactions done")

        df["Category"] = categories
        st.success("🎉 Done! Here's the result:")
        st.dataframe(df[[desc_col, "Category"]])

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Categorized CSV", csv, "categorized_transactions.csv", "text/csv")
