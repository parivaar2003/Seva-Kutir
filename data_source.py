# data_source.py
import pandas as pd
from datetime import datetime, timedelta
from statistics import mean

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
        # Load from Excel
        self.sheet = pd.read_excel('Parivaar_Kutirs_MocK_Data.xlsx', sheet_name='Mock_Data')
        self.rename_columns()
        self.make_columns_unique()
        self.convert_column_types()
        self.precompute_periods()

    def rename_columns(self):
        rename_map = {}
        for col in self.sheet.columns:
            # Use 'in' for robustness against slight variations in column names if any
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
            elif 'Date' in col: # Ensure Date column is consistently named
                rename_map[col] = 'Date'
            elif 'Timestamp' in col:
                rename_map[col] = 'Timestamp'
            elif 'Datetime' in col:
                rename_map[col] = 'Datetime'


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
                counts[col] = 0 # Initialize count for new column
                new_columns.append(col)
        self.sheet.columns = new_columns

    def convert_column_types(self):
        date_time_cols = ['Timestamp', 'Datetime', 'Date']
        integer_cols = ['Teachers Phone Number', 'Attendance of Students']
        
        # Prioritize 'Date' column for conversion if it exists
        if 'Date' in self.sheet.columns:
            self.sheet['Date'] = pd.to_datetime(self.sheet['Date'], errors='coerce')
        
        # Convert other potential datetime columns
        for col in date_time_cols:
            if col != 'Date' and col in self.sheet.columns:
                self.sheet[col] = pd.to_datetime(self.sheet[col], errors='coerce')
        
        for col in integer_cols:
            if col in self.sheet.columns:
                self.sheet[col] = pd.to_numeric(self.sheet[col], errors='coerce')
                # Fill NaN attendance with 0 after conversion, if appropriate for your data
                self.sheet[col] = self.sheet[col].fillna(0)


    def precompute_periods(self):
        df = self.sheet

        # Ensure 'Date' column is datetime
        if 'Date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Date']):
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Drop rows where 'Date' is NaT after conversion
        df.dropna(subset=['Date'], inplace=True)
        if df.empty:
            self.sheet = df
            self.week_ranges = pd.DataFrame(columns=['Weekly Period', 'Week Start Date', 'Week End Date'])
            return


        df['Daily Period'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Monthly Period'] = df['Date'].dt.strftime('%Y-%m')
        df['Yearly Period'] = df['Date'].dt.strftime('%Y')

        iso = df['Date'].dt.isocalendar()
        df['ISO_Year'] = iso.year
        df['ISO_Week'] = iso.week
        # Corrected: Use .str.zfill(2) for string formatting on Series
        df['Weekly Period'] = df['ISO_Year'].astype(str) + '-W' + df['ISO_Week'].astype(str).str.zfill(2)

        # Calculate Week Start and End Dates for each unique Weekly Period
        week_start_end_map = {}
        unique_weekly_periods = df[['ISO_Year', 'ISO_Week']].drop_duplicates().sort_values(['ISO_Year', 'ISO_Week'])

        for index, row in unique_weekly_periods.iterrows():
            year = int(row['ISO_Year'])
            week = int(row['ISO_Week'])
            
            # Corrected: Use Period string for pd.Period constructor
            period_label = f"{year}-W{str(week).zfill(2)}"
            try:
                week_period = pd.Period(period_label, freq='W-MON') # Week starts on Monday
            except ValueError:
                # Handle cases where period_label might be invalid (e.g., week 0 or week 53 in some years)
                # This might indicate bad data or edge cases with ISO calendar
                print(f"Warning: Could not create Period for {period_label}. Skipping.")
                continue
            
            week_start_date = week_period.start_time.date()
            week_end_date = week_period.end_time.date() # end_time is Sunday 23:59:59.999...

            week_start_end_map[period_label] = {
                'Week Start Date': pd.Timestamp(week_start_date),
                'Week End Date': pd.Timestamp(week_end_date)
            }
        
        self.week_ranges = pd.DataFrame.from_dict(week_start_end_map, orient='index').reset_index()
        self.week_ranges.rename(columns={'index': 'Weekly Period'}, inplace=True)

        # Merge week start and end into df
        self.sheet = df.merge(self.week_ranges, on='Weekly Period', how='left')

    def aggregate_attendance(self, df, frequency):
        df_copy = df.copy() # Work on a copy
        
        # Ensure 'Date' column is datetime before proceeding
        if 'Date' not in df_copy.columns or not pd.api.types.is_datetime64_any_dtype(df_copy['Date']):
             # If Date column is missing or not datetime, return empty DFs
             return pd.DataFrame(), pd.DataFrame()
        
        # Normalize 'Date' to remove time component, ensuring each day is treated as a single entity
        df_copy['Date'] = df_copy['Date'].dt.normalize()

        if frequency == "Daily":
            df_copy['Period'] = df_copy['Daily Period']
            # Detailed df is sum of attendance per session per day
            detailed_df = df_copy.groupby(['Period', 'Date', 'Kutir Name', 'Type of Kutir', 'State', 'District', 'Cluster'], as_index=False)['Attendance of Students'].sum().reset_index()
            agg_df = detailed_df.groupby('Period')['Attendance of Students'].sum().reset_index()

        elif frequency == "Weekly":
            df_copy['Period'] = df_copy['Weekly Period']

            # Step 1: Calculate daily total attendance per Kutir
            # This crucial step now sums all shifts for a given day for a kutir
            required_cols_daily = ['Period', 'Date', 'Kutir Name', 'Type of Kutir', 'State', 'District', 'Cluster', 'Attendance of Students'] # Removed 'Shift' from here
            if not all(col in df_copy.columns for col in required_cols_daily):
                print(f"Warning: Missing required columns for weekly daily_kutir_attendance. Required: {required_cols_daily}, Found: {df_copy.columns.tolist()}")
                return pd.DataFrame(), pd.DataFrame()

            daily_kutir_attendance = df_copy.groupby(['Period', 'Date', 'Kutir Name', 'Type of Kutir', 'State', 'District', 'Cluster'], as_index=False)['Attendance of Students'].sum()
            daily_kutir_attendance.rename(columns={'Attendance of Students': 'Daily Attendance'}, inplace=True)
            
            # Detailed DF for other charts (Kutir Type vs Period)
            # This should contain original data points or daily sums per kutir
            detailed_df = daily_kutir_attendance.merge(self.week_ranges, left_on='Period', right_on='Weekly Period', how='left')
            detailed_df.rename(columns={'Daily Attendance': 'Attendance of Students'}, inplace=True) # Renaming for consistency with plotting functions

            # Step 2: Calculate weekly average attendance for EACH KUTIR based on days present
            weekly_kutir_avg = daily_kutir_attendance.groupby(['Period', 'Kutir Name'], as_index=False).agg(
                sum_daily_attendance=('Daily Attendance', 'sum'),
                count_days=('Date', 'nunique') # This correctly counts unique days
            )
            
            print(weekly_kutir_avg)
            
            # Handle division by zero for weeks with no data if count_days is 0
            weekly_kutir_avg['Kutir Weekly Avg Attendance'] = weekly_kutir_avg.apply(
                lambda row: row['sum_daily_attendance'] / row['count_days'] if row['count_days'] > 0 else 0, axis=1
            )

            # Step 3: Calculate the overall average weekly attendance (average of kutir weekly averages)
            # This is the 'agg_df' for the main trend chart and KPIs
            agg_df = weekly_kutir_avg.groupby('Period', as_index=False)['Kutir Weekly Avg Attendance'].mean()
            agg_df.rename(columns={'Kutir Weekly Avg Attendance': 'Attendance of Students'}, inplace=True)
            
            agg_df = agg_df.merge(self.week_ranges, left_on='Period', right_on='Weekly Period', how='left')


        elif frequency == "Monthly":
            df_copy['Period'] = df_copy['Monthly Period']
            # For monthly, if you want daily sums first, similar logic applies as weekly
            # but for now, it's summing all sessions for the month
            detailed_df = df_copy.groupby(['Period', 'Date', 'Kutir Name', 'Type of Kutir', 'State', 'District', 'Cluster'], as_index=False)['Attendance of Students'].sum()
            agg_df = detailed_df.groupby('Period')['Attendance of Students'].sum().reset_index()


        elif frequency == "Yearly":
            df_copy['Period'] = df_copy['Yearly Period']
            # Similar to monthly, sums all sessions for the year
            detailed_df = df_copy.groupby(['Period', 'Date', 'Kutir Name', 'Type of Kutir', 'State', 'District', 'Cluster'], as_index=False)['Attendance of Students'].sum()
            agg_df = detailed_df.groupby('Period')['Attendance of Students'].sum().reset_index()

        else:
            detailed_df = pd.DataFrame()
            agg_df = pd.DataFrame()

        return agg_df, detailed_df
    
    def aggregate_kutir_attendance(self, detailed_df, frequency):
        if detailed_df.empty:
            return pd.DataFrame()

        if frequency == "Weekly":
            required_cols_kutir_agg = ['Period', 'Type of Kutir', 'Kutir Name', 'Attendance of Students', 'Date']
            if not all(col in detailed_df.columns for col in required_cols_kutir_agg):
                print(f"Warning: Missing required columns for weekly aggregate_kutir_attendance. Required: {required_cols_kutir_agg}, Found: {detailed_df.columns.tolist()}")
                return pd.DataFrame()

            # detailed_df for weekly already holds daily sums per kutir (due to aggregate_attendance change)
            # So, now group by Period, Type of Kutir, Kutir Name to sum these daily sums and count days
            daily_attendance_per_kutir_type = detailed_df.groupby(['Period', 'Type of Kutir', 'Kutir Name'], as_index=False).agg(
                sum_daily_attendance=('Attendance of Students', 'sum'), # This is the sum of daily sums for a kutir in a week
                count_days=('Date', 'nunique') # Count unique days for each kutir in that week
            )
            daily_attendance_per_kutir_type['Kutir Weekly Avg Attendance'] = daily_attendance_per_kutir_type.apply(
                lambda row: row['sum_daily_attendance'] / row['count_days'] if row['count_days'] > 0 else 0, axis=1
            )
            
            agg_kutir_df = daily_attendance_per_kutir_type.groupby(['Period', 'Type of Kutir'], as_index=False)['Kutir Weekly Avg Attendance'].mean()
            agg_kutir_df.rename(columns={'Kutir Weekly Avg Attendance': 'Attendance of Students'}, inplace=True)

            agg_kutir_df = agg_kutir_df.merge(self.week_ranges, left_on='Period', right_on='Weekly Period', how='left')

        else:
            required_cols_non_weekly = ['Period', 'Type of Kutir', 'Attendance of Students']
            if not all(col in detailed_df.columns for col in required_cols_non_weekly):
                print(f"Warning: Missing required columns for non-weekly aggregate_kutir_attendance. Required: {required_cols_non_weekly}, Found: {detailed_df.columns.tolist()}")
                return pd.DataFrame()

            agg_kutir_df = detailed_df.groupby(['Period', 'Type of Kutir'], as_index=False)['Attendance of Students'].sum()

        return agg_kutir_df


    def calculate_kpis(self, agg_df):
        periods = agg_df['Period'].nunique() if not agg_df.empty else 0
        max_attendance = agg_df['Attendance of Students'].max() if not agg_df.empty else 0
        avg_attendance = agg_df['Attendance of Students'].mean() if not agg_df.empty else 0

        return periods, max_attendance, avg_attendance

    def categorize(self, attendance):
        if pd.isna(attendance):
            return 'Unknown'
        if attendance < 50:
            return '<50'
        elif 50 <= attendance <= 75:
            return '50-75'
        elif 76 <= attendance <= 100:
            return '76-100'
        else:
            return '100+'
