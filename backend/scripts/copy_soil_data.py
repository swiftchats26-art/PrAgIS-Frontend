import csv
from pathlib import Path

# Read the soil data from the original file
original_data = []
with open('c:\\Users\\Nayan\\Desktop\\AI-FARMING\\soil_data.csv', 'r') as f:
    reader = csv.reader(f)
    original_data = list(reader)

# Write it to the backend directory
output_path = Path('c:\\Users\\Nayan\\Desktop\\AI-FARMING\\backend\\soil_data.csv')
with open(output_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(original_data)