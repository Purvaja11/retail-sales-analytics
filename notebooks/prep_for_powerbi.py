import pandas as pd

df = pd.read_csv('retail-sales-analytics/data/superstore.csv', encoding='latin-1')
df['Order Date'] = pd.to_datetime(df['Order Date'], format='%m/%d/%Y')
df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%m/%d/%Y')
df.to_csv('retail-sales-analytics/data/superstore_clean.csv', index=False)
print("✅ Clean CSV saved — dates fixed for Power BI")
print(df.dtypes[['Order Date', 'Ship Date']])
