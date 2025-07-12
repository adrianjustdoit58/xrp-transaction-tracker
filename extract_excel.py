import pandas as pd
import json

# Load the Excel file
file_path = '/Users/adria/Desktop/Crypto Fraud/250711 Crypto Theft Overview.xlsx'
excel_data = pd.ExcelFile(file_path)

# Extract data from all sheets
data = {}
for sheet in excel_data.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet)
    data[sheet] = df.to_dict(orient='records')

# Output as JSON
print(json.dumps(data, default=str))