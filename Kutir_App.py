# Kutir_App.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from data_source import data
import pandas as pd

st.set_page_config(page_title="Seva Kutir Dashboard", layout="wide")
st.markdown("""
    <h1 style='text-align: center; color: #4A4A4A;'>Seva Kutir Monitoring Dashboard</h1>
""", unsafe_allow_html=True)

# Load data
data_object = data()
df = data_object.sheet

# Filter Section (inline below title)
st.markdown("### Filters")
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    selected_state = st.selectbox('Select State', sorted(df['State'].dropna().unique()))
with col2:
    selected_district = st.selectbox('Select District', sorted(df[df['State'] == selected_state]['District'].dropna().unique()))
with col3:
    selected_cluster = st.selectbox('Select Cluster', sorted(df[df['District'] == selected_district]['Cluster'].dropna().unique()))
with col4:
    selected_kutir = st.selectbox('Select Kutir type', sorted(df[df['Cluster'] == selected_cluster]['Type of Kutir'].dropna().unique()))
with col5:
    start_date = st.date_input('Select Start Date', value=df['Date'].min().date())
with col6:
    end_date = st.date_input('Select End Date', value=df['Date'].max().date())
with col7:
    frequency = st.selectbox("Select Frequency", ["Daily", "Weekly", "Monthly", "Yearly"])

filtered_df = df[(df['State'] == selected_state) &
                 (df['District'] == selected_district) &
                 (df['Cluster'] == selected_cluster) &
                 (df['Type of Kutir'] == selected_kutir) &
                 (df['Date'].dt.date >= start_date) &
                 (df['Date'].dt.date <= end_date)]

# KPI Section
st.markdown("""
<style>
.metric-card {
    background-color: #F0F2F6;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

st.markdown("### Key Performance Indicators")
kpi1, kpi2, kpi3 = st.columns(3)

agg_df = data_object.aggregate_attendance(filtered_df, frequency)
periods = agg_df['Period'].nunique()
max_students = agg_df['Attendance of Students'].max()
avg_attendance = agg_df['Attendance of Students'].mean()

period_label = "Days" if frequency == "Daily" else "Weeks" if frequency == "Weekly" else "Months" if frequency == "Monthly" else "Years"

with kpi1:
    st.markdown(f"""
        <div class='metric-card'>
            <h3>Total No of {period_label}</h3>
            <h2>{periods}</h2>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class='metric-card'>
            <h3>Max Attendance in a {period_label[:-1]}</h3>
            <h2>{int(max_students) if not pd.isna(max_students) else 0}</h2>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class='metric-card'>
            <h3>{frequency} Avg Attendance</h3>
            <h2>{avg_attendance:.2f}</h2>
        </div>
    """, unsafe_allow_html=True)

# Graph 1: Attendance Trend Chart
st.markdown(f"### Student Attendance Over Time ({frequency} Basis)")
fig1 = px.line(agg_df, x='Period', y='Attendance of Students', title=f"Student Attendance vs Period ({frequency})")
fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20))

if frequency == "Daily":
    fig1.update_xaxes(dtick="D1", tickformat="%Y-%m-%d")
elif frequency == "Weekly":
    fig1.update_xaxes(dtick="M1", tickformat="%Y-%W")
elif frequency == "Monthly":
    fig1.update_xaxes(dtick="M1", tickformat="%Y-%m")
elif frequency == "Yearly":
    fig1.update_xaxes(dtick="M12", tickformat="%Y")

st.plotly_chart(fig1, use_container_width=True)

# Graph 2: Kutir Type vs Period
st.markdown(f"### Kutir Type Attendance Trend ({frequency} Basis)")
kt_df = filtered_df.copy()
if frequency == "Daily":
    kt_df['Period'] = kt_df['Date'].dt.strftime('%Y-%m-%d')
elif frequency == "Weekly":
    kt_df['Period'] = kt_df['Date'].dt.strftime('%Y-%U')
elif frequency == "Monthly":
    kt_df['Period'] = kt_df['Date'].dt.strftime('%Y-%m')
elif frequency == "Yearly":
    kt_df['Period'] = kt_df['Date'].dt.strftime('%Y')

kt_agg_df = kt_df.groupby(['Period', 'Type of Kutir'], as_index=False)['Attendance of Students'].sum()
fig2 = px.bar(kt_agg_df, x='Period', y='Attendance of Students', color='Type of Kutir', barmode='group',
              title=f"Kutir Type vs Period ({frequency})")

if frequency == "Daily":
    fig2.update_xaxes(dtick="D1", tickformat="%Y-%m-%d")
elif frequency == "Weekly":
    fig2.update_xaxes(dtick="M1", tickformat="%Y-%W")
elif frequency == "Monthly":
    fig2.update_xaxes(dtick="M1", tickformat="%Y-%m")
elif frequency == "Yearly":
    fig2.update_xaxes(dtick="M12", tickformat="%Y")

fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20))
st.plotly_chart(fig2, use_container_width=True)

# Detailed Table
st.markdown("### Detailed Session Data")
st.dataframe(filtered_df[['Date', 'Shift', 'Teachers Name', 'Attendance of Students', 'Type of Kutir', 'Kutir Name']])
