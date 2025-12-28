import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Holiday Maximizer", layout="wide")

st.title("🌴 AI Holiday Maximizer (India 2018 Edition)")
st.markdown("""
Maximize your vacation time! This tool finds the best holiday + weekend combinations
based on your Indian holiday dataset.
""")

# ---------------- DATA LOADING ----------------
@st.cache_data
def load_and_process_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = [c.lower().strip() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])

    all_dates = pd.date_range(df["date"].min(), df["date"].max())
    calendar = pd.DataFrame({"date": all_dates})
    calendar["is_weekend"] = calendar["date"].dt.weekday.isin([5, 6])

    df = calendar.merge(df, on="date", how="left")
    df["holiday"] = df["holiday"].fillna("Working Day")
    df["is_holiday"] = df["holiday"] != "Working Day"
    df["is_free"] = df["is_weekend"] | df["is_holiday"]
    df["month"] = df["date"].dt.strftime("%B")

    return df

data = load_and_process_data("2018.csv")

# ---------------- ALGORITHM ----------------
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
                    "Start Date": df.iloc[i]["date"],
                    "End Date": df.iloc[j]["date"],
                    "Duration": duration,
                    "PTO Cost": pto_needed,
                    "Efficiency": round(efficiency, 2),
                    "Month": df.iloc[i]["month"]
                })

    return pd.DataFrame(results).sort_values(
        ["Efficiency", "Duration"], ascending=False
    )

# ---------------- SIDEBAR ----------------
st.sidebar.header("Preferences")
annual_pto = st.sidebar.slider("Annual PTO Budget", 0, 30, 15)

options = get_global_rankings(data, annual_pto)

# ---------------- GLOBAL TABLE ----------------
st.header("📊 Global Holiday Rankings")

if not options.empty:
    st.dataframe(
        options.head(20),
        width="stretch"
    )
else:
    st.warning("No valid combinations found.")

# ---------------- PERSONAL SEARCH ----------------
st.divider()
st.header("🔍 Personalized Vacation Search")

col1, col2, col3 = st.columns(3)

with col1:
    search_pto = st.number_input("Max PTO for trip", 0, 10, 1)

with col2:
    min_days = st.number_input("Minimum break length", 1, 15, 4)

with col3:
    search_month = st.selectbox("Month", sorted(options["Month"].unique()))

if st.button("Search"):
    matches = options[
        (options["Month"] == search_month) &
        (options["PTO Cost"] <= search_pto) &
        (options["Duration"] >= min_days)
    ]

    if not matches.empty:
        best = matches.iloc[0]
        st.success("✅ Combination Found!")
        st.write(f"📅 {best['Start Date'].date()} → {best['End Date'].date()}")
        st.write(f"🕒 {best['Duration']} days")
        st.write(f"🏖 PTO Cost: {best['PTO Cost']}")
    else:
        st.error("No matching combination found.")

# ---------------- VISUALIZATIONS ----------------
st.divider()
st.header("📈 Holiday Insights")

tab1, tab2 = st.tabs(["Efficiency Plot", "Timeline View"])

with tab1:
    if not options.empty:
        fig, ax = plt.subplots()
        ax.scatter(options["Duration"], options["Efficiency"])
        ax.set_xlabel("Duration (days)")
        ax.set_ylabel("Efficiency")
        st.pyplot(fig)

with tab2:
    if not options.empty:
        top10 = options.head(10).sort_values("Start Date")

        fig, ax = plt.subplots(figsize=(12, 5))
        for i, row in enumerate(top10.itertuples()):
            start = row._1
            end = row._2
            ax.barh(i, (end - start).days, left=start)

        ax.set_yticks(range(len(top10)))
        ax.set_yticklabels([d.strftime("%b %d") for d in top10["Start Date"]])
        ax.set_xlabel("Date")
        ax.set_title("Top 10 Holiday Timelines")
        st.pyplot(fig)
