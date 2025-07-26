import streamlit as st
import pandas as pd
import openai
import time
from ratelimit import limits, sleep_and_retry

# Load OpenAI key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# OpenAI rate limit for gpt-4.1-mini
MAX_REQUESTS_PER_MINUTE = 450

# GPT model
MODEL = "gpt-4-1106-preview"  # GPT-4.1-mini

# Define allowed categories
CATEGORIES = ["Drinking", "Groceries", "Transport", "Shopping", "Health", 
              "Cafe", "Food & Dining", "Lodging", "Transfers", "Entertainment", "Other"]

# Prompt template
def make_prompt(description):
    return (
        f"This is a transaction from a bank: '{description}'. "
        f"What type of business is this likely to be? "
        f"Pick ONE category from this list: {', '.join(CATEGORIES)}. "
        "Only reply with the category name."
    )

# Rate-limited GPT call
@sleep_and_retry
@limits(calls=MAX_REQUESTS_PER_MINUTE, period=60)
def classify_transaction(description):
    try:
        prompt = make_prompt(description)
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        category = response.choices[0].message.content.strip()
        return category, prompt, response.usage.total_tokens
    except Exception as e:
        return f"Error: {e}", description, 0

# Streamlit UI
st.title("🧠 GPT-Powered Transaction Categorizer")
st.markdown("Upload a CSV with a column named `Description` to auto-categorize using GPT-4.1-mini.")

uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if "Description" not in df.columns:
        st.error("CSV must contain a 'Description' column.")
    else:
        results = []
        logs = []
        total_tokens = 0

        with st.spinner("Processing transactions..."):
            for i, row in df.iterrows():
                desc = str(row["Description"])
                category, prompt, tokens_used = classify_transaction(desc)
                total_tokens += tokens_used
                results.append(category)
                logs.append({"Prompt": prompt, "Response": category})

        df["Category"] = results
        st.success("Done!")
        st.dataframe(df)

        st.markdown("### 🪵 Debug Log")
        for i, log in enumerate(logs):
            st.markdown(f"**Transaction {i+1}**")
            st.code(f"Prompt: {log['Prompt']}")
            st.code(f"Response: {log['Response']}")

        st.markdown(f"**Total tokens used:** {total_tokens}")

        # Optional: download results
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Categorized CSV", csv, "categorized_transactions.csv", "text/csv")
