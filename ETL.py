import numpy as np
import pandas as pd
import os

folder_path = '/Users/robby/PycharmProjects/ACCTMIS_4650/Source_Data'

# Get all files in the folder
all_files = os.listdir(folder_path)
print(all_files)

# Sort files by order of appearance
all_files = sorted(all_files, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
print(all_files)

# For each file in the folder, add to the list of DataFrames
dataframes = []
for file in all_files:
    file_path = os.path.join(folder_path, file)
    df = pd.read_csv(file_path)
    dataframes.append(df)

# Combine all DataFrames
combined_df = pd.concat(dataframes)

# Assuming combined_df is your DataFrame with a 'YEAR' column
periods = [
    (combined_df['YEAR'] < 2020),  # Before Covid
    (combined_df['YEAR'] >= 2020) & (combined_df['YEAR'] <= 2021),  # During Covid
    (combined_df['YEAR'] > 2021)  # After Covid
]

# Labels for the periods
labels = ['Before Covid', 'During Covid', 'After Covid']

# Adding a new column 'COVID_PERIOD' based on the 'YEAR' column
combined_df['COVID_PERIOD'] = np.select(periods, labels, default='Unknown')

# keep only columbus origin and destination flight entries
City = 'Columbus, OH'
combined_df = combined_df.loc[(combined_df['ORIGIN_CITY_NAME'] == City) |
                              (combined_df['DEST_CITY_NAME'] == City)]

# combining year and month together to make date
combined_df['YEAR'] = combined_df['YEAR'].astype(int)
combined_df['MONTH'] = combined_df['MONTH'].astype(int)

combined_df['DATE'] = pd.to_datetime(combined_df[['YEAR', 'MONTH']].assign(DAY=1))

# getting rid of unnecessary data
# combined_df = combined_df.drop(columns=['YEAR', 'MONTH'], inplace=False)

# Check the DataFrame contents
print(combined_df.head(5))  # First 5 rows
print(combined_df.tail(5))  # Last 5 rows

# Save to local Excel and CSV
combined_df.to_excel('Master_Flight_File.xlsx', index=False)
combined_df.to_csv('Master_Flight_File.csv', index=False)


"""
Making the star schema output files
"""
# Time dimension
time_dim = combined_df[['DATE', 'YEAR', 'QUARTER', 'MONTH', 'COVID_PERIOD']].drop_duplicates()
time_dim.rename(columns={'DATE': 'TimeKey'}, inplace=True)
time_dim.to_csv("/Users/robby/PycharmProjects/ACCTMIS_4650/Output_Data/time_dim.csv", index=False)

# Carrier dimension
carrier_dim = combined_df[['UNIQUE_CARRIER', 'UNIQUE_CARRIER_NAME']].drop_duplicates()
carrier_dim['CarrierKey'] = carrier_dim.index + 1  # Adding unique key
carrier_dim = carrier_dim[['CarrierKey', 'UNIQUE_CARRIER', 'UNIQUE_CARRIER_NAME']]  # Reorder columns
carrier_dim.to_csv("/Users/robby/PycharmProjects/ACCTMIS_4650/Output_Data/carrier_dim.csv", index=False)

# Origin dimension
origin_dim = combined_df[['ORIGIN_AIRPORT_ID', 'ORIGIN', 'ORIGIN_CITY_NAME', 'ORIGIN_STATE_ABR']].drop_duplicates()
origin_dim.rename(columns={'ORIGIN_AIRPORT_ID': 'OriginKey'}, inplace=True)
origin_dim.to_csv("/Users/robby/PycharmProjects/ACCTMIS_4650/Output_Data/origin_dim.csv", index=False)

# Destination dimension
destination_dim = combined_df[['DEST_AIRPORT_ID', 'DEST', 'DEST_CITY_NAME', 'DEST_STATE_ABR']].drop_duplicates()
destination_dim.rename(columns={'DEST_AIRPORT_ID': 'DestKey'}, inplace=True)
destination_dim.to_csv("/Users/robby/PycharmProjects/ACCTMIS_4650/Output_Data/destination_dim.csv", index=False)

"""
Fact Table Construction
1. Merging combined df with dimension tables
2. Adding foreign keys and measures
"""
# before merge check
print("Left DataFrame Columns:", combined_df.columns)
print("Origin Dimension Columns:", origin_dim.columns)

# Merge
fact_table = combined_df.merge(time_dim,
                               left_on='DATE',
                               right_on='TimeKey',
                               how='left') \
    .merge(carrier_dim,
           on=['UNIQUE_CARRIER', 'UNIQUE_CARRIER_NAME'],
           how='left') \
    .merge(origin_dim,
           left_on=['ORIGIN', 'ORIGIN_CITY_NAME', 'ORIGIN_STATE_ABR'],
           right_on=['ORIGIN', 'ORIGIN_CITY_NAME', 'ORIGIN_STATE_ABR'],
           how='left') \
    .merge(destination_dim,
           left_on=['DEST', 'DEST_CITY_NAME', 'DEST_STATE_ABR'],
           right_on=['DEST', 'DEST_CITY_NAME', 'DEST_STATE_ABR'],
           how='left')

# after merge check
print("Original rows:", len(combined_df))
print("Rows after merge:", len(fact_table))

# Adding foreign keys and measures
fact_table = fact_table[['TimeKey', 'CarrierKey', 'OriginKey', 'DestKey', 'PASSENGERS', 'DISTANCE']]

# get rid of duplicate compound keys in fact table
fact_table = fact_table.drop_duplicates(subset=['TimeKey', 'CarrierKey', 'OriginKey', 'DestKey'])
print("Number of rows after duplicate keys removed: ", len(fact_table))

fact_table.to_csv("/Users/robby/PycharmProjects/ACCTMIS_4650/Output_Data/fact_table.csv", index=False)
fact_table.to_excel('Fact_Table.xlsx', index=False)

# pick fact table row and find matching dimension entry
