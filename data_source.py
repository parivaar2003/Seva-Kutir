# data_source.py
import pandas as pd
from datetime import datetime
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
        # print("Original Columns:", self.sheet.columns.tolist())  # Debug line
        self.rename_columns()
        self.make_columns_unique()
        self.convert_column_types()

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

    def filter_data(self, state, district):
        return self.sheet[
            (self.sheet['State'] == state) &
            (self.sheet['District'] == district)
        ]

    def aggregate_attendance(self, df, frequency):
        df = df.copy()
        if frequency == "Daily":
            df['Period'] = df['Date'].dt.strftime('%Y-%m-%d')
        elif frequency == "Weekly":
            df['Period'] = df['Date'].dt.strftime('%Y-W%U')
        elif frequency == "Monthly":
            df['Period'] = df['Date'].dt.strftime('%Y-%m')
        elif frequency == "Yearly":
            df['Period'] = df['Date'].dt.strftime('%Y')

        agg_df = df.groupby('Period', as_index=False)['Attendance of Students'].sum()
        return agg_df, df

    def calculate_kpis(self, df):
        total_sessions = df.shape[0]
        avg_attendance = df['Attendance of Students'].mean()
        return total_sessions, avg_attendance
