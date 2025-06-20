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

# Top-right reload button
reload_col = st.columns([0.85, 0.15])[1]
with reload_col:
    if st.button("🔄 Reload Data"):
        data.destroy_instance()
        st.experimental_rerun()

# Load data
data_object = data()
df = data_object.sheet
filtered_df = df.copy()

# Filters
st.markdown("### Filters")
# Row 1: State and Date Range
row1_col1, row1_col2, row1_col3, row1_col4, row1_col5 = st.columns(5)
with row1_col1:
    selected_state = st.selectbox('Select State', sorted(df['State'].dropna().unique()), index=1)
    filtered_df = filtered_df[filtered_df['State'] == selected_state]
with row1_col2:
    start_date = st.date_input('Start Date', value=filtered_df['Date'].min().date())
    filtered_df = filtered_df[filtered_df['Date'].dt.date >= start_date]
with row1_col3:
    end_date = st.date_input('End Date', value=filtered_df['Date'].max().date(), min_value=start_date)
    if end_date < start_date:
        st.warning("End Date cannot be before Start Date. Resetting End Date to Start Date.")
        end_date = start_date
    filtered_df = filtered_df[filtered_df['Date'].dt.date <= end_date]
with row1_col4:
    selected_shift = st.selectbox('Select Shift', sorted(df['Shift'].dropna().unique()))
    filtered_df = filtered_df[filtered_df['Shift'] == selected_shift]
with row1_col5:
    frequency = st.selectbox("Select Frequency", ["Daily", "Weekly", "Monthly", "Yearly"], index=1)

# Row 2: District, Cluster, Kutir Name, Kutir Type
row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)

# Multiselect for District
with row2_col1:
    district_options = sorted(filtered_df['District'].dropna().unique())
    district_options.insert(0, "All")
    selected_districts = st.multiselect("Select District(s)", district_options, default=["All"])
    if 'All' not in selected_districts:
        filtered_df = filtered_df[filtered_df['District'].isin(selected_districts)]


# Multiselect for Cluster (filtered by selected districts)
with row2_col2:
    cluster_options = filtered_df['Cluster'].dropna().unique()
    cluster_options = sorted(cluster_options)
    cluster_options.insert(0, "All")
    selected_clusters = st.multiselect("Select Cluster(s)", cluster_options, default=["All"])
    if 'All' not in selected_clusters:
        filtered_df = filtered_df[filtered_df['Cluster'].isin(selected_clusters)]

# Multiselect for Kutir Name
with row2_col3:
    kutir_name_options = filtered_df['Kutir Name'].dropna().unique()
    kutir_name_options = sorted(kutir_name_options)
    kutir_name_options.insert(0, "All")
    selected_kutir_names = st.multiselect("Select Kutir Name(s)", kutir_name_options, default=["All"])
    if 'All' not in selected_kutir_names:
        filtered_df = filtered_df[filtered_df['Kutir Name'].isin(selected_kutir_names)]

# Multiselect for Kutir Type
with row2_col4:
    kutir_types = sorted(filtered_df['Type of Kutir'].dropna().unique())
    selected_kutirs = st.multiselect('Select Kutir Type', options=["All"] + kutir_types, default=["All"])
    if "All" not in selected_kutirs:
        filtered_df = filtered_df[filtered_df['Type of Kutir'].isin(selected_kutirs)]

# KPI Section
st.markdown("""<style>
.metric-card {
    background-color: #F0F2F6;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.05);
}
</style>""", unsafe_allow_html=True)

st.markdown("### Key Performance Indicators")
kpi1, kpi2, kpi3 = st.columns(3)

agg_df, detailed_df = data_object.aggregate_attendance(filtered_df, frequency)
periods, max_students, avg_attendance = data_object.calculate_kpis(agg_df)

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

# Attendance Trend Chart
st.markdown(f"### Student Attendance Over Time ({frequency} Basis)")

attendance_export_df = agg_df[['Period', 'Attendance of Students']].copy()
if frequency == "Weekly" and 'Week Start Date' in agg_df.columns:
    attendance_export_df = agg_df[['Period', 'Attendance of Students', 'Week Start Date', 'Week End Date']]

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

# Kutir Type vs Period
## Prepare data for export
agg_kutir_df = data_object.aggregate_kutir_attendance(detailed_df, frequency)

## Create Excel in-memory
export_buffer = BytesIO()
agg_kutir_df.to_excel(export_buffer, index=False, engine='xlsxwriter')
export_buffer.seek(0)

## Download button for export
st.download_button(
    label="Download Kutir Type Attendance Data",
    data=export_buffer,
    file_name="kutir_type_attendance_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

## fig2
# Custom color mapping for Kutir Types
kutir_color_map = {
    "Study Center": "#160642",  # Blue
    "Seva Kutir": "#aec7e8",     # Light Blue
    "Shiksha Kutir": "#4c78a8", # Darker Blue
    # Add more mappings if more types exist
}

# Use only colors that are in the data
types_in_data = agg_kutir_df['Type of Kutir'].unique()
color_map_filtered = {k: v for k, v in kutir_color_map.items() if k in types_in_data}

# fig2
fig2 = px.bar(
    agg_kutir_df,
    x='Period',
    y='Attendance of Students',
    color='Type of Kutir',
    color_discrete_map=color_map_filtered,
    barmode='stack',
    title=f"Kutir Type vs Period ({frequency})"
)
fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20))
fig2.update_xaxes(type='category', tickangle=45)
st.plotly_chart(fig2, use_container_width=True)
#------------------------------------------------------------------------------------------------------
# Aggregate attendance by District and Period
kutir_latest_period = sorted(detailed_df['Period'].dropna().unique())[-2:]
kutir_latest_df = detailed_df[detailed_df['Period'].isin(kutir_latest_period)]
kutir_latest_df['District'] = kutir_latest_df['District'] +'-'+ kutir_latest_df['Period']

fig3a_df = kutir_latest_df.groupby(['District', 'Kutir Name'])['Attendance of Students'].sum().reset_index()

fig3a_df['Attendance Category'] = fig3a_df['Attendance of Students'].apply(data_object.categorize)

attendance_bins_by_district = (
    fig3a_df.groupby(['District', 'Attendance Category'])
    .size()
    .unstack(fill_value=0)
    .reindex(columns=['<50', '50-75', '76-100', '100+'], fill_value=0)  # Ensure all categories appear
    .reset_index()
)
avg_attendance_per_district = (
    fig3a_df.groupby('District')['Attendance of Students']
    .mean()
    .reset_index()
    .rename(columns={'Attendance of Students': 'Average Attendance'})
)
fig3_df = pd.merge(attendance_bins_by_district, avg_attendance_per_district, on='District')

excel_buffer = BytesIO()
fig3_df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
excel_buffer.seek(0)
st.download_button(
    label="Download Data as Excel",
    data=excel_buffer,
    file_name="District_Kurit_Attendance_Bucket.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Group by both District and Attendance Category
attendance_bins_by_district_2 = (
    fig3a_df.groupby(['District', 'Attendance Category'])
            .size()
            .reset_index(name='Number of Kutirs')
)

# Optional: sort category labels
attendance_bins_by_district_2['Attendance Category'] = pd.Categorical(
    attendance_bins_by_district_2['Attendance Category'],
    categories=['<50', '50-75', '76-100', '100+'],
    ordered=True
)
# Pivot for horizontal bar chart
fig3 = px.bar(
    attendance_bins_by_district_2,
    x='District',
    y='Number of Kutirs',
    color='Attendance Category',
    barmode='stack',
    title=f'Kutir Attendance Category Distribution by District({frequency})'
)
st.plotly_chart(fig3, use_container_width=True)
#------------------------------------------------------------------------------------------------------
# Detailed Table
st.markdown("### Detailed Session Data")
columns_to_display = st.multiselect("Select Columns to Display", options=filtered_df.columns.tolist(), default=['Date', 'Shift', 'Teachers Name', 'Attendance of Students', 'Type of Kutir', 'Kutir Name'])
excel_buffer = BytesIO()
filtered_df[columns_to_display].to_excel(excel_buffer, index=False, engine='xlsxwriter')
excel_buffer.seek(0)
st.download_button(
    label="Download Data as Excel",
    data=excel_buffer,
    file_name="filtered_kutir_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.dataframe(filtered_df[columns_to_display])