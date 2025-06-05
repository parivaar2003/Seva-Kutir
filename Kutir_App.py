# Kutir_App.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from data_source import data
import pandas as pd
from io import BytesIO

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
    start_date = st.date_input('Select Start Date', value=df['Date'].min().date())
with col5:
    end_date = st.date_input('Select End Date', value=df['Date'].max().date())
with col6:
    frequency = st.selectbox("Select Frequency", ["Daily", "Weekly", "Monthly", "Yearly"], index=1)
with col7:
    selected_shift = st.selectbox('Select Shift', sorted(df['Shift'].dropna().unique()))

# Kutir type on a separate row
selected_kutirs = st.multiselect('Select Kutir type', sorted(df[df['Cluster'] == selected_cluster]['Type of Kutir'].dropna().unique()))

# Filtering
df = df[(df['State'] == selected_state) &
        (df['District'] == selected_district) &
        (df['Cluster'] == selected_cluster) &
        (df['Shift'] == selected_shift) &
        (df['Date'].dt.date >= start_date) &
        (df['Date'].dt.date <= end_date)]
if selected_kutirs:
    df = df[df['Type of Kutir'].isin(selected_kutirs)]

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

agg_df, agg_df_2 = data_object.aggregate_attendance(df, frequency)
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

# Create period-attendance dataframe with date ranges for weekly
attendance_export_df = agg_df[['Period', 'Attendance of Students']].copy()
if frequency == "Weekly":
    week_date_range = df.copy()
    week_date_range['Week'] = week_date_range['Date'].dt.strftime('%U').astype(int)
    week_date_range['Year'] = week_date_range['Date'].dt.year
    week_date_range['Period'] = week_date_range['Year'].astype(str) + '-W' + week_date_range['Week'].astype(str).str.zfill(2)
    range_map = (
        week_date_range.groupby('Period')['Date']
        .agg(['min', 'max'])
        .rename(columns={'min': 'Week Start Date', 'max': 'Week End Date'})
        .reset_index()
    )
    attendance_export_df = attendance_export_df.merge(range_map, on='Period', how='left')

# Download button for period-attendance dataframe
excel_attendance_buffer = BytesIO()
attendance_export_df.to_excel(excel_attendance_buffer, index=False, engine='xlsxwriter')
excel_attendance_buffer.seek(0)
st.download_button(
    label="Download Attendance Trend Data",
    data=excel_attendance_buffer,
    file_name="attendance_trend_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

agg_df['Color'] = agg_df['Attendance of Students'].apply(lambda x: 'red' if x < avg_attendance else 'blue')
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=agg_df['Period'],
    y=agg_df['Attendance of Students'],
    mode='lines+markers',
    line=dict(color='gray'),
    marker=dict(color=agg_df['Color']),
    name='Attendance'
))
fig1.add_trace(go.Scatter(
    x=agg_df[agg_df['Color'] == 'red']['Period'],
    y=agg_df[agg_df['Color'] == 'red']['Attendance of Students'],
    mode='markers',
    marker=dict(color='red', size=10),
    name=f'Below {frequency} Average'
))
fig1.add_trace(go.Scatter(
    x=agg_df[agg_df['Color'] == 'blue']['Period'],
    y=agg_df[agg_df['Color'] == 'blue']['Attendance of Students'],
    mode='markers',
    marker=dict(color='blue', size=10),
    name=f'Above {frequency} Average'
))
fig1.update_layout(title=f"Student Attendance vs Period ({frequency})",
                   margin=dict(l=20, r=20, t=40, b=20))
fig1.update_xaxes(type='category', tickangle=45)
st.plotly_chart(fig1, use_container_width=True)

# Graph 2: Kutir Type vs Period
st.markdown(f"### Kutir Type Attendance Trend ({frequency} Basis)")
fig2 = px.bar(agg_df_2, x='Period', y='Attendance of Students', color='Type of Kutir', barmode='group',
              title=f"Kutir Type vs Period ({frequency})")
fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20))
fig2.update_xaxes(type='category', tickangle=45)
st.plotly_chart(fig2, use_container_width=True)

# Detailed Table
st.markdown("### Detailed Session Data")
columns_to_display = st.multiselect("Select Columns to Display", options=df.columns.tolist(), default=['Date', 'Shift', 'Teachers Name', 'Attendance of Students', 'Type of Kutir', 'Kutir Name'])
st.dataframe(df[columns_to_display])

excel_buffer = BytesIO()
df[columns_to_display].to_excel(excel_buffer, index=False, engine='xlsxwriter')
excel_buffer.seek(0)
st.download_button(
    label="Download Data as Excel",
    data=excel_buffer,
    file_name="filtered_kutir_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
