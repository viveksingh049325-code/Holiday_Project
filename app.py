import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Holiday Maximizer", layout="wide")

st.title("🌴 AI Holiday Maximizer — India")
st.caption("Plan smarter vacations by combining weekends, holidays, and minimal PTO.")

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Vacation Preferences")

include_rh = st.sidebar.checkbox(
    "Include Restricted Holidays (RH)",
    value=True,
    help="If unchecked, RH will be treated as working days"
)

year = st.sidebar.selectbox(
    "Select Year",
    options=[2018, 2026, 2027],
    index=0
)

annual_pto = st.sidebar.slider("Annual PTO Budget", 0, 30, 15)

# ---------------- DATA LOADING ----------------
@st.cache_data
def load_and_process_data(file_path, include_rh):
    df = pd.read_csv(file_path)
    df.columns = [c.lower().strip() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])

    all_dates = pd.date_range(df["date"].min(), df["date"].max())
    calendar = pd.DataFrame({"date": all_dates})
    calendar["is_weekend"] = calendar["date"].dt.weekday.isin([5, 6])

    df = calendar.merge(df, on="date", how="left")
    df["holiday"] = df["holiday"].fillna("Working Day")
    df["is_restricted"] = df["holiday"].str.contains(r"\(RH\)", regex=True)

    if include_rh:
        df["is_holiday"] = df["holiday"] != "Working Day"
    else:
        df["is_holiday"] = (df["holiday"] != "Working Day") & (~df["is_restricted"])

    df["is_free"] = df["is_weekend"] | df["is_holiday"]
    df["month"] = df["date"].dt.strftime("%B")

    return df

# ---------------- ALGORITHM (FIXED 0-PTO LOGIC) ----------------
def get_global_rankings(df, pto_limit):
    results = []
    n = len(df)

    for i in range(n):
        if not df.iloc[i]["is_free"]:
            continue

        for j in range(i + 1, n):
            window = df.iloc[i:j + 1]
            pto_needed = (~window["is_free"]).sum()

            if pto_needed > pto_limit:
                break

            if df.iloc[j]["is_free"]:
                duration = j - i + 1
                # 🚫 Skip plain 2-day weekends
                if duration <= 2 and pto_needed == 0 and window["is_holiday"].sum() == 0:
                    continue

                # ✅ CORRECT 0-PTO HANDLING
                if pto_needed == 0:
                    efficiency = float("inf")
                else:
                    efficiency = duration / pto_needed

                results.append({
                    "Start Date": df.iloc[i]["date"],
                    "End Date": df.iloc[j]["date"],
                    "Duration": duration,
                    "PTO Cost": pto_needed,
                    "Efficiency": efficiency,
                    "Month": df.iloc[i]["month"]
                })

    results_df = pd.DataFrame(results)

    if results_df.empty:
        return results_df

    # Sort correctly: 0-PTO (∞) first, then longer duration
    results_df = results_df.sort_values(
        by=["Efficiency", "Duration"],
        ascending=[False, False]
    )

    # Display-friendly efficiency
    results_df["Efficiency Display"] = results_df["Efficiency"].apply(
        lambda x: "∞ (No PTO)" if x == float("inf") else round(x, 2)
    )

    return results_df

# ---------------- DATA EXECUTION ----------------
csv_file = f"{year}.csv"
if not os.path.exists(csv_file):
    st.error(f"Holiday data for {year} not available.")
    st.stop()

data = load_and_process_data(csv_file, include_rh)
options = get_global_rankings(data, annual_pto)

# ---------------- GLOBAL RESULTS ----------------
st.header("📊 Best Holiday Combinations")

if not options.empty:
    best = options.iloc[0]
    st.success("🏆 Best Overall Recommendation")
    st.write(f"📅 {best['Start Date'].date()} → {best['End Date'].date()}")
    st.write(f"🕒 {best['Duration']} days | PTO: {best['PTO Cost']}")

    st.dataframe(
        options[[
            "Start Date", "End Date", "Duration",
            "PTO Cost", "Efficiency Display", "Month"
        ]],
        width="stretch"
    )

    st.download_button(
        "⬇ Download All Results (CSV)",
        options.to_csv(index=False).encode("utf-8"),
        f"holiday_rankings_{year}.csv",
        "text/csv"
    )
else:
    st.warning("No valid combinations found.")

# ---------------- PERSONALIZED SEARCH ----------------
st.divider()
st.header("🔍 Personalized Vacation Search")

col1, col2, col3 = st.columns(3)

with col1:
    search_pto = st.number_input("Max PTO for trip", 0, 10, 1)

with col2:
    min_days = st.number_input("Minimum break length", 1, 15, 4)

with col3:
    search_month = st.selectbox(
        "Month",
        sorted(options["Month"].unique()) if not options.empty else []
    )

if st.button("Search"):
    matches = options[
        (options["Month"] == search_month) &
        (options["PTO Cost"] <= search_pto) &
        (options["Duration"] >= min_days)
    ]

    if not matches.empty:
        best_match = matches.iloc[0]

        st.success("🏆 Best Personalized Recommendation")
        st.write(f"📅 {best_match['Start Date'].date()} → {best_match['End Date'].date()}")
        st.write(f"🕒 {best_match['Duration']} days | PTO: {best_match['PTO Cost']}")

        if len(matches) > 1:
            st.subheader("Other Valid Options")
            st.dataframe(
                matches.iloc[1:10][[
                    "Start Date", "End Date", "Duration",
                    "PTO Cost", "Efficiency Display"
                ]],
                width="stretch"
            )
    else:
        st.error("No matching combinations found.")

# ---------------- VISUALS ----------------
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
            ax.barh(i, (row.End_Date - row.Start_Date).days, left=row.Start_Date)

        ax.set_yticks(range(len(top10)))
        ax.set_yticklabels([d.strftime("%b %d") for d in top10["Start Date"]])
        ax.set_title("Top 10 Holiday Timelines")
        st.pyplot(fig)
