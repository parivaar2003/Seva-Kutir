# Kutir_App.py
import streamlit as st
from data_source import data
import plotly.graph_objects as go

# Initialize the data object
data_object = data()
df = data_object.sheet

st.title("Seva Kutir Attendance Dashboard")

# Sidebar filters
st.sidebar.header("Filters")
selected_state = st.sidebar.selectbox("Select a State", options=sorted(df['State'].dropna().unique()))
filtered_districts = df[df['State'] == selected_state]['District'].dropna().unique()
selected_district = st.sidebar.selectbox("Select a District", options=sorted(filtered_districts))
frequency = st.sidebar.selectbox("Select Frequency", options=["Daily", "Monthly", "Yearly"])

# Filter data
filtered_df = data_object.filter_data(selected_state, selected_district)
agg_df = data_object.aggregate_attendance(filtered_df, frequency)

# KPIs
total_sessions, avg_attendance = data_object.calculate_kpis(filtered_df)

st.metric(label="Total Sessions", value=total_sessions)
st.metric(label="Average Attendance", value=f"{avg_attendance:.2f}")

# Plotting chart
fig = go.Figure()
fig.add_trace(go.Bar(
    x=agg_df['Period'],
    y=agg_df['Attendance of Students'],
    marker_color='lightskyblue',
))
fig.update_layout(
    title=f"Attendance Over Time ({frequency})",
    xaxis_title="Period",
    yaxis_title="Total Attendance",
    xaxis_tickangle=-45,
    template='plotly_white'
)

st.plotly_chart(fig, use_container_width=True)
