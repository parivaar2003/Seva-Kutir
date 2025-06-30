# Kutir_App.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from data_source import data
import pandas as pd
from io import BytesIO
from datetime import timedelta
from datetime import datetime

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
    state_options = sorted(df['State'].dropna().unique().tolist())
    
    # Determine the default index for 'Madhya Pradesh'
    default_state_name = 'Madhya Pradesh'
    try:
        default_index = state_options.index(default_state_name)
    except ValueError:
        default_index = 0 # Fallback to the first state if 'Madhya Pradesh' is not found

    if not state_options:
        state_options = ["No Data"]
        selected_state = "No Data"
        st.warning("No state data available.")
    else:
        selected_state = st.selectbox('Select State', state_options, index=default_index) # Set default state here
    
    if selected_state != "No Data":
        filtered_df = filtered_df[filtered_df['State'] == selected_state]
    else:
        filtered_df = pd.DataFrame() # No data if no state selected


with row1_col2:
    # Ensure min/max values are based on the filtered_df after state selection
    # Add check for empty filtered_df to prevent errors
    if not filtered_df.empty and 'Date' in filtered_df.columns and pd.api.types.is_datetime64_any_dtype(filtered_df['Date']):
        min_date_available = filtered_df['Date'].min().date() if pd.notna(filtered_df['Date'].min()) else datetime.now().date()
        max_date_available = filtered_df['Date'].max().date() if pd.notna(filtered_df['Date'].max()) else datetime.now().date()
    else:
        min_date_available = datetime.now().date()
        max_date_available = datetime.now().date()

    start_date = st.date_input('Start Date', value=min_date_available)
    if not filtered_df.empty:
        filtered_df = filtered_df[filtered_df['Date'].dt.date >= start_date]

with row1_col3:
    if not filtered_df.empty and 'Date' in filtered_df.columns and pd.api.types.is_datetime64_any_dtype(filtered_df['Date']):
        # Recalculate max_date_available after start_date filtering
        current_max_date = filtered_df['Date'].max().date() if pd.notna(filtered_df['Date'].max()) else datetime.now().date()
        if current_max_date < start_date:
            current_max_date = start_date
    else:
        current_max_date = start_date

    end_date = st.date_input('End Date', value=current_max_date, min_value=start_date)
    if end_date < start_date:
        st.warning("End Date cannot be before Start Date. Resetting End Date to Start Date.")
        end_date = start_date
    if not filtered_df.empty:
        filtered_df = filtered_df[filtered_df['Date'].dt.date <= end_date]

with row1_col4:
    shift_options = sorted(df['Shift'].dropna().unique().tolist())
    shift_options.insert(0, "All Shifts") # Add "All Shifts" option
    
    selected_shift = st.selectbox('Select Shift', shift_options, index=0) # Default to "All Shifts"
    
    if selected_shift != "All Shifts":
        filtered_df = filtered_df[filtered_df['Shift'] == selected_shift]
    # No else needed if "All Shifts" is selected, as filtered_df remains as is
    if filtered_df.empty and selected_shift != "All Shifts": # Show warning only if specific shift selected and no data
        st.warning("No data for selected shift.")

with row1_col5:
    frequency = st.selectbox("Select Frequency", ["Daily", "Weekly", "Monthly", "Yearly"], index=1)

# Row 2: District, Cluster, Kutir Name, Kutir Type
row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)

with row2_col1:
    district_options = sorted(filtered_df['Districts'].dropna().unique().tolist())
    district_options.insert(0, "All")
    selected_districts = st.multiselect("Select District(s)", district_options, default=["All"])
    if 'All' not in selected_districts:
        filtered_df = filtered_df[filtered_df['District'].isin(selected_districts)]
    if filtered_df.empty and "All" not in selected_districts:
        st.warning("No data for selected districts.")


with row2_col2:
    cluster_options = filtered_df['Cluster'].dropna().unique().tolist()
    cluster_options = sorted(cluster_options)
    cluster_options.insert(0, "All")
    selected_clusters = st.multiselect("Select Cluster(s)", cluster_options, default=["All"])
    if 'All' not in selected_clusters:
        filtered_df = filtered_df[filtered_df['Cluster'].isin(selected_clusters)]
    if filtered_df.empty and "All" not in selected_clusters:
        st.warning("No data for selected clusters.")

with row2_col3:
    kutir_name_options = filtered_df['Kutir Name'].dropna().unique().tolist()
    kutir_name_options = sorted(kutir_name_options)
    kutir_name_options.insert(0, "All")
    selected_kutir_names = st.multiselect("Select Kutir Name(s)", kutir_name_options, default=["All"])
    if 'All' not in selected_kutir_names:
        filtered_df = filtered_df[filtered_df['Kutir Name'].isin(selected_kutir_names)]
    if filtered_df.empty and "All" not in selected_kutir_names:
        st.warning("No data for selected Kutir Names.")

with row2_col4:
    kutir_types = sorted(filtered_df['Type of Kutir'].dropna().unique().tolist())
    selected_kutirs = st.multiselect('Select Kutir Type', options=["All"] + kutir_types, default=["All"])
    if "All" not in selected_kutirs:
        filtered_df = filtered_df[filtered_df['Type of Kutir'].isin(selected_kutirs)]
    if filtered_df.empty and "All" not in selected_kutirs:
        st.warning("No data for selected Kutir Types.")

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
            <h3>Max Attendance in a {period_label[:-1] if period_label != 'Days' else 'Day'}</h3>
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

st.markdown(f"### Student Attendance Over Time ({frequency} Basis)")

if not agg_df.empty:
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

    # Add horizontal line for average attendance
    fig1.add_hline(
        y=avg_attendance, 
        line_dash="dot",
        annotation_text=f"Avg: {avg_attendance:.2f}", 
        annotation_position="bottom right",
        line_color="green"
    )

    fig1.update_layout(title=f"Student Attendance vs Period ({frequency})",
                    margin=dict(l=20, r=20, t=40, b=20))
    fig1.update_xaxes(type='category', tickangle=45)
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("No data available to display Attendance Trend Chart for the selected filters.")

agg_kutir_df = data_object.aggregate_kutir_attendance(detailed_df, frequency)

if not agg_kutir_df.empty:
    export_buffer = BytesIO()
    agg_kutir_df.to_excel(export_buffer, index=False, engine='xlsxwriter')
    export_buffer.seek(0)

    st.download_button(
        label="Download Kutir Type Attendance Data",
        data=export_buffer,
        file_name="kutir_type_attendance_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    kutir_color_map = {
        "Study Center": "#160642",
        "Seva Kutir": "#aec7e8",
        "Shiksha Kutir": "#4c78a8",
    }

    types_in_data = agg_kutir_df['Type of Kutir'].unique()
    color_map_filtered = {k: v for k, v in kutir_color_map.items() if k in types_in_data}

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
else:
    st.info("No data available to display Kutir Type vs Period Chart for the selected filters.")

st.markdown(f"### Kutir Attendance Category Distribution by District ({frequency})")

fig3a_df = pd.DataFrame()

if not detailed_df.empty:
    if frequency == "Weekly":
        required_cols_fig3_weekly = ['Period', 'Date', 'Kutir Name', 'District', 'Attendance of Students']
        if not all(col in detailed_df.columns for col in required_cols_fig3_weekly):
            st.warning("Missing columns in detailed_df for weekly district distribution for Fig3. Skipping.")
        else:
            daily_kutir_district_attendance = detailed_df.groupby(['Period', 'Date', 'Kutir Name', 'District'], as_index=False)['Attendance of Students'].sum()
            
            weekly_avg_per_kutir_district = daily_kutir_district_attendance.groupby(['Period', 'Kutir Name', 'District'], as_index=False).agg(
                sum_daily_attendance=('Attendance of Students', 'sum'),
                count_days=('Date', 'nunique')
            )
            weekly_avg_per_kutir_district['Kutir Weekly Avg Attendance'] = weekly_avg_per_kutir_district.apply(
                lambda row: row['sum_daily_attendance'] / row['count_days'] if row['count_days'] > 0 else 0, axis=1
            )
            
            latest_periods = sorted(weekly_avg_per_kutir_district['Period'].dropna().unique(), reverse=True)[:2]
            kutir_latest_df = weekly_avg_per_kutir_district[weekly_avg_per_kutir_district['Period'].isin(latest_periods)].copy()
            
            if not data_object.week_ranges.empty:
                kutir_latest_df = kutir_latest_df.merge(data_object.week_ranges[['Weekly Period', 'Week Start Date', 'Week End Date']], 
                                                        left_on='Period', right_on='Weekly Period', how='left')
                
                kutir_latest_df['Week Start Date Display'] = kutir_latest_df['Week Start Date'].dt.strftime('%Y-%m-%d').fillna('')
                kutir_latest_df['Week End Date Display'] = kutir_latest_df['Week End Date'].dt.strftime('%Y-%m-%d').fillna('')

                kutir_latest_df['District_Period_Label'] = kutir_latest_df['District'] + '-' + kutir_latest_df['Week Start Date Display'] + ' to ' + kutir_latest_df['Week End Date Display']
            else:
                kutir_latest_df['District_Period_Label'] = kutir_latest_df['District'] + '-' + kutir_latest_df['Period']
                
            fig3a_df = kutir_latest_df.groupby(['District_Period_Label', 'Kutir Name'])['Kutir Weekly Avg Attendance'].mean().reset_index()
            fig3a_df.rename(columns={'Kutir Weekly Avg Attendance': 'Attendance of Students', 'District_Period_Label': 'District'}, inplace=True)

    else:
        if 'Period' not in detailed_df.columns:
            st.warning("Period column missing in detailed_df for non-weekly frequency in Fig3.")
        else:
            kutir_latest_period = sorted(detailed_df['Period'].dropna().unique(), reverse=True)[:2]
            kutir_latest_df = detailed_df[detailed_df['Period'].isin(kutir_latest_period)].copy()

            if not kutir_latest_df.empty:
                kutir_latest_df['District_Period_Label'] = kutir_latest_df['District'] +'-'+ kutir_latest_df['Period']
                fig3a_df = kutir_latest_df.groupby(['District_Period_Label', 'Kutir Name'])['Attendance of Students'].sum().reset_index()
                fig3a_df.rename(columns={'District_Period_Label': 'District'}, inplace=True)

if not fig3a_df.empty:
    fig3a_df['Attendance Category'] = fig3a_df['Attendance of Students'].apply(data_object.categorize)

    # Define the categories to ensure consistent ordering and handling of missing categories
    CATEGORIES = ['<50', '50-75', '76-100', '100+', 'Unknown']

    attendance_bins_by_district = (
        fig3a_df.groupby(['District', 'Attendance Category'])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=CATEGORIES, fill_value=0)
        .reset_index()
    )
    if 'Attendance of Students' in fig3a_df.columns:
        avg_attendance_per_district = (
            fig3a_df.groupby('District')['Attendance of Students']
            .mean()
            .reset_index()
            .rename(columns={'Attendance of Students': 'Average Attendance'})
        )
    else:
        avg_attendance_per_district = pd.DataFrame(columns=['District', 'Average Attendance'])

    fig3_df = pd.merge(attendance_bins_by_district, avg_attendance_per_district, on='District', how='left')

    excel_buffer = BytesIO()
    fig3_df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
    excel_buffer.seek(0)
    st.download_button(
        label="Download Data as Excel",
        data=excel_buffer,
        file_name="District_Kurit_Attendance_Bucket.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- NEW, MORE ROBUST LOGIC for creating the chart's dataframe ---
    # 1. Group and pivot to wide format, ensuring all districts are kept
    wide_df_for_chart = (
        fig3a_df.groupby(['District', 'Attendance Category'])
                .size()
                .unstack(fill_value=0)
    )
    # 2. Reindex to ensure all category columns exist, adding any that are missing
    wide_df_for_chart = wide_df_for_chart.reindex(columns=CATEGORIES, fill_value=0)

    # 3. Melt the guaranteed-complete dataframe back to a long format suitable for plotting
    attendance_bins_by_district_2 = wide_df_for_chart.reset_index().melt(
        id_vars='District',
        var_name='Attendance Category',
        value_name='Number of Kutirs'
    )
    
    # This part remains the same, ensuring the legend is ordered correctly
    attendance_bins_by_district_2['Attendance Category'] = pd.Categorical(
        attendance_bins_by_district_2['Attendance Category'],
        categories=CATEGORIES,
        ordered=True
    )

    fig3 = px.bar(
        attendance_bins_by_district_2,
        x='District',
        y='Number of Kutirs',
        color='Attendance Category',
        barmode='stack',
        title=f'Kutir Attendance Category Distribution by District({frequency})'
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No data available to display Kutir Attendance Category Distribution for the selected filters.")

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
