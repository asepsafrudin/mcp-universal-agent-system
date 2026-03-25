
import json
import os

source_file = "/home/aseps/MCP/storage/admin_data/korespondensi/korespondensi_sekretariat_eksternal_data.json"
dest_file = "/home/aseps/MCP/storage/admin_data/korespondensi/korespondensi surat masuk ke bangda.json"

if not os.path.exists(source_file):
    print(f"Error: {source_file} not found")
    exit(1)

with open(source_file, 'r') as f:
    data = json.load(f)

values = data.get("values", [])
if not values:
    print("Error: No data values found")
    exit(1)

header = values[0]
rows = values[1:]

restructured_data = []
for row in rows:
    # Skip rows that are too short or mostly empty
    if len(row) < 2 or not any(row):
        continue
    
    # Optional: Skip the dummy row if it looks like empty/template
    # In the sample, row 1 was ["", "", "", "", "", "", "", "", "0001/L", "Selesai"]
    if len(row) > 1 and not row[1] and not row[2]:
        continue

    item = {}
    for i, column_name in enumerate(header):
        if i < len(row):
            val = row[i]
            # Convert "null" string to None or empty string
            if isinstance(val, str) and val.lower() == "null":
                val = ""
            item[column_name] = val
        else:
            item[column_name] = ""
    restructured_data.append(item)

# Save the new format
output = {
    "spreadsheet_id": data.get("spreadsheet_id"),
    "range": data.get("range"),
    "synced_at": data.get("synced_at"),
    "total_rows": len(restructured_data),
    "data": restructured_data
}

with open(dest_file, 'w') as f:
    json.dump(output, f, indent=2)

print(f"Successfully created {dest_file} with {len(restructured_data)} items.")
