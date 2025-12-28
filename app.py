import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Holiday Maximizer", layout="wide")

st.title("🌴 AI Holiday Maximizer (India 2018 Edition)")
st.markdown("Optimize your vacations using Indian public holidays and weekends.")

@st.cache_data
def load_data():
    df = pd.read_csv("2018.csv")
    df.columns = [c.lower().strip() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])

    calendar = pd.DataFrame({
        "date": pd.date_range(df["date"].min(), df["date"].max())
    })
    calendar["is_weekend"] = calendar["date"].dt.weekday.isin([5, 6])

    df = calendar.merge(df, on="date", how="left")
    df["holiday"] = df["holiday"].fillna("Working Day")
    df["is_holiday"] = df["holiday"] != "Working Day"
    df["is_free"] = df["is_weekend"] | df["is_holiday"]
    df["month"] = df["date"].dt.strftime("%B")
    return df

data = load_data()

def get_global_rankings(df, pto_limit):
    results = []
    n = len(df)
    for i in range(n):
        if not df.iloc[i]["is_free"]:
            continue
        for j in range(i + 2, n):
            window = df.iloc[i:j+1]
            pto_needed = (~window["is_free"]).sum()
            if pto_needed > pto_limit:
                break
            if df.iloc[j]["is_free"]:
                duration = j - i + 1
                efficiency = duration / max(pto_needed, 1)
                results.append({
                    "Start Date": df.iloc[i]["date"].date(),
                    "End Date": df.iloc[j]["date"].date(),
                    "Duration": duration,
                    "PTO Cost": pto_needed,
                    "Efficiency": round(efficiency, 2),
                    "Month": df.iloc[i]["date"].strftime("%B")
                })
    return pd.DataFrame(results).sort_values(
        ["Efficiency", "Duration"], ascending=False
    )

st.sidebar.header("Preferences")
annual_pto = st.sidebar.slider("Annual PTO Budget", 0, 30, 15)

options = get_global_rankings(data, annual_pto)

st.subheader("📊 Best Holiday Combinations")
st.dataframe(options.head(20), use_container_width=True)

# --- SAFE PLOT (no seaborn) ---
st.subheader("📈 Efficiency Plot")

import matplotlib.pyplot as plt   # delayed import (SAFE)

fig, ax = plt.subplots()
ax.scatter(options["Duration"], options["Efficiency"])
ax.set_xlabel("Duration (days)")
ax.set_ylabel("Efficiency")
st.pyplot(fig)
