# data_source.py
import pandas as pd
from datetime import datetime, timedelta
from statistics import mean
from oauth2client.service_account import ServiceAccountCredentials

# Singleton decorator for caching
def singleton(cls):
    instances = {}
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    def destroy_instance():
        if cls in instances:
            del instances[cls]
    wrapper.destroy_instance = destroy_instance
    return wrapper

@singleton
class data:
    def __init__(self):
        self.sheet = pd.read_excel('Parivaar_Kutirs_Mock_Data.xlsx', sheet_name='Mock_Data')
        self.rename_columns()
        self.make_columns_unique()
        self.convert_column_types()
        self.precompute_periods()

    def rename_columns(self):
        rename_map = {}
        for col in self.sheet.columns:
            if 'Teachers Name' in col:
                rename_map[col] = 'Teachers Name'
            elif 'Teachers Phone Number' in col:
                rename_map[col] = 'Teachers Phone Number'
            elif 'Shift' in col:
                rename_map[col] = 'Shift'
            elif 'Attendance of Students' in col:
                rename_map[col] = 'Attendance of Students'
            elif 'Type of Kutir' in col:
                rename_map[col] = 'Type of Kutir'
            elif 'State' in col:
                rename_map[col] = 'State'
            elif 'District' in col:
                rename_map[col] = 'District'
            elif 'Cluster' in col:
                rename_map[col] = 'Cluster'
            elif 'Kutir Name' in col:
                rename_map[col] = 'Kutir Name'

        self.sheet.rename(columns=rename_map, inplace=True)

    def make_columns_unique(self):
        columns = self.sheet.columns
        counts = {}
        new_columns = []
        for col in columns:
            if col in counts:
                counts[col] += 1
                new_columns.append(f"{col}.{counts[col]}")
            else:
                counts[col] = 0
                new_columns.append(col)
        self.sheet.columns = new_columns

    def convert_column_types(self):
        date_time_cols = ['Timestamp', 'Datetime', 'Date']
        integer_cols = ['Teachers Phone Number', 'Attendance of Students']
        for col in date_time_cols:
            if col in self.sheet.columns:
                self.sheet[col] = pd.to_datetime(self.sheet[col], errors='coerce')
        for col in integer_cols:
            if col in self.sheet.columns:
                self.sheet[col] = pd.to_numeric(self.sheet[col], errors='coerce')

    def precompute_periods(self):
        df = self.sheet

        df['Daily Period'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Monthly Period'] = df['Date'].dt.strftime('%Y-%m')
        df['Yearly Period'] = df['Date'].dt.strftime('%Y')

        iso = df['Date'].dt.isocalendar()
        df['ISO_Year'] = iso.year
        df['ISO_Week'] = iso.week
        df['Weekly Period'] = df['ISO_Year'].astype(str) + '-W' + df['ISO_Week'].astype(str).str.zfill(2)

        week_ranges = df.groupby('Weekly Period')['Date'].agg(['min', 'max']).reset_index()
        week_ranges.rename(columns={'min': 'Week Start Date', 'max': 'Week End Date'}, inplace=True)
        # Merge week start and end into df
        df = df.merge(week_ranges, on='Weekly Period', how='left')

        # Assign back to self
        self.sheet = df
        self.week_ranges = week_ranges

    def filter_data(self, state=None, district=None, cluster=None, shift=None, kutir=None, start_date=None, end_date=None):
        df = self.sheet

        if state:
            df = df[df['State'] == state]
        if district:
            df = df[df['District'] == district]
        if cluster:
            df = df[df['Cluster'] == cluster]
        if shift:
            df = df[df['Shift'] == shift]
        if start_date and end_date:
            df = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)]
        if kutir:
            df = df[df['Type of Kutir'].isin(kutir)]

        return df

    def aggregate_attendance(self, df, frequency):
        if frequency == "Daily":
            df['Period'] = df['Daily Period']
        elif frequency == "Weekly":
            df['Period'] = df['Weekly Period']
        elif frequency == "Monthly":
            df['Period'] = df['Monthly Period']
        elif frequency == "Yearly":
            df['Period'] = df['Yearly Period']

        agg_df = df.groupby('Period', as_index=False)['Attendance of Students'].sum()

        if frequency == "Weekly":
            agg_df = agg_df.merge(self.week_ranges, left_on='Period', right_on='Weekly Period', how='left')

        return agg_df, df
    
    def aggregate_kutir_attendance(self, df, frequency):
        """
        Aggregates attendance by Period and Type of Kutir.
        If Weekly, includes Week Start and End Dates.
        """
        agg_kutir_df = df.groupby(['Period', 'Type of Kutir'], as_index=False)['Attendance of Students'].sum()

        if frequency == "Weekly" and 'Week Start Date' in df.columns and 'Week End Date' in df.columns:
            agg_kutir_df = agg_kutir_df.merge(self.week_ranges, left_on='Period', right_on='Weekly Period', how='left')

        return agg_kutir_df


    def calculate_kpis(self, agg_df):
        # Weekly KPI calculation based on aggregated data
        num_weeks = agg_df.shape[0]
        max_attendance = agg_df['Attendance of Students'].max()
        avg_weekly_attendance = agg_df['Attendance of Students'].mean()

        return num_weeks, max_attendance, avg_weekly_attendance
