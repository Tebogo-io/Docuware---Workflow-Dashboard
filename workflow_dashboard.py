# workflow_dashboard.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier

# -------------------------
# ⚙️ PAGE CONFIG
# -------------------------
st.set_page_config(layout="wide")

# -------------------------
# 🎨 SIMPLE STYLING (SaaS feel)
# -------------------------
st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

# -------------------------
# 📂 LOAD DATA
# -------------------------
df = pd.read_csv(
    r"C:\Users\gkteb\Documents\Workflow Prediction Model\workflow_data.csv",
    sep=';'
)

# -------------------------
# 🧠 DATA PREP
# -------------------------
df["completion_time"] = pd.to_datetime(df["completion_time"])
df = df.sort_values(by=["workflow_ID", "completion_time"])

df["step_duration"] = (
    df.groupby("workflow_ID")["completion_time"]
    .diff()
    .dt.total_seconds()
)

df["step_duration"] = df["step_duration"].fillna(0)

# -------------------------
# 🚨 BOTTLENECK DETECTION
# -------------------------
threshold = df["step_duration"].quantile(0.9)
df["is_bottleneck"] = df["step_duration"] > threshold

# -------------------------
# 🔮 ML MODEL (WORKFLOW LEVEL)
# -------------------------
df_workflow = df.groupby("workflow_ID").agg({
    "step_duration": ["sum", "mean", "max"],
    "step_name": "count"
})

df_workflow.columns = [
    "total_duration",
    "avg_step_time",
    "max_step_time",
    "num_steps"
]

df_workflow = df_workflow.reset_index()

# Create target
delay_threshold = df_workflow["total_duration"].quantile(0.75)
df_workflow["delayed"] = df_workflow["total_duration"] > delay_threshold

# Train model
X = df_workflow.drop(columns=["workflow_ID", "delayed"])
y = df_workflow["delayed"]

model = RandomForestClassifier(class_weight="balanced", random_state=42)
model.fit(X, y)

# -------------------------
# 🤖 AI EXPLANATION FUNCTION
# -------------------------
def explain_workflow(timeline_df):
    slow_steps = timeline_df.sort_values(by="step_duration", ascending=False).head(3)

    explanation = "This workflow is slow mainly due to:\n\n"

    for _, row in slow_steps.iterrows():
        explanation += f"- {row['step_name']} took {int(row['step_duration'])} seconds\n"

    explanation += "\nThese steps contribute the most to the delay."

    return explanation

# -------------------------
# 🎛️ SIDEBAR
# -------------------------
st.sidebar.title("Filters")

workflow_filter = st.sidebar.multiselect(
    "Select workflow(s)",
    options=df["workflow_ID"].unique(),
    default=df["workflow_ID"].unique()
)

df_filtered = df[df["workflow_ID"].isin(workflow_filter)].copy()

# -------------------------
# 🎯 TITLE
# -------------------------
st.title("🚀 Workflow Intelligence Dashboard")
st.markdown("AI-powered bottleneck detection and workflow prediction")
st.markdown("---")

# -------------------------
# 🎯 SELECT WORKFLOW
# -------------------------
selected_workflow = st.selectbox(
    "Select workflow to analyze",
    df_filtered["workflow_ID"].unique()
)

timeline_df = df_filtered[df_filtered["workflow_ID"] == selected_workflow].copy()

# -------------------------
# 📊 KPI CARDS
# -------------------------
col1, col2, col3 = st.columns(3)

col1.metric("📊 Total Steps", len(timeline_df))
col2.metric("⏱ Total Duration", f"{int(timeline_df['step_duration'].sum())} sec")
col3.metric("🚨 Bottlenecks", int(timeline_df["is_bottleneck"].sum()))

st.markdown("---")

# -------------------------
# 🔮 PREDICTION
# -------------------------
current = df_workflow[df_workflow["workflow_ID"] == selected_workflow]

prediction = model.predict(current.drop(columns=["workflow_ID", "delayed"]))

st.subheader("🔮 Workflow Prediction")

if prediction[0] == 1:
    st.error("⚠️ This workflow is likely to be delayed")
else:
    st.success("✅ This workflow is running normally")

# -------------------------
# 🤖 AI INSIGHT
# -------------------------
st.subheader("🤖 AI Insight")

if st.button("Explain Workflow Performance"):
    st.info(explain_workflow(timeline_df))

st.markdown("---")

# -------------------------
# 📈 ROW 1: GRAPHS
# -------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Slowest Steps")

    step_perf = (
        df_filtered.groupby("step_name")["step_duration"]
        .mean()
        .sort_values(ascending=False)
    )

    fig1, ax1 = plt.subplots()
    step_perf.head(10).plot(kind="bar", ax=ax1)
    plt.xticks(rotation=45)
    plt.ylabel("Seconds")
    st.pyplot(fig1)

with col2:
    st.subheader("Step Type Performance")

    step_type_perf = (
        df_filtered.groupby("step_type")["step_duration"]
        .mean()
        .sort_values(ascending=False)
    )

    fig2, ax2 = plt.subplots()
    step_type_perf.plot(kind="bar", ax=ax2)
    plt.ylabel("Seconds")
    st.pyplot(fig2)

st.markdown("---")

# -------------------------
# ⏱️ TIMELINE
# -------------------------
st.subheader("Workflow Timeline")

timeline_df["start_time"] = (
    timeline_df.groupby("workflow_ID")["completion_time"].shift(1)
)

timeline_df["start_time"] = timeline_df["start_time"].fillna(
    timeline_df["completion_time"]
)

fig = px.timeline(
    timeline_df,
    x_start="start_time",
    x_end="completion_time",
    y="step_name",
    color="is_bottleneck"
)

fig.update_yaxes(autorange="reversed")

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# -------------------------
# 📋 TABLES
# -------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Bottlenecks")

    st.dataframe(
        timeline_df[timeline_df["is_bottleneck"]]
        .sort_values(by="step_duration", ascending=False)
        [["step_name", "step_duration"]]
        .head(10)
    )

with col2:
    st.subheader("Critical Steps")

    st.dataframe(
        timeline_df
        .sort_values(by="step_duration", ascending=False)
        [["step_name", "step_duration"]]
        .head(10)
    )

st.markdown("---")

# -------------------------
# 📊 SUMMARY
# -------------------------
st.subheader("Bottlenecks per Workflow")

bottleneck_counts = df_filtered.groupby("workflow_ID")["is_bottleneck"].sum()
st.bar_chart(bottleneck_counts)