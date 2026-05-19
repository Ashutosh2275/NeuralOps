import os

# Fix IncidentDetail.tsx (e: any => to (e: any) =>)
file = "frontend/src/pages/IncidentDetail.tsx"
with open(file, "r", encoding="utf-8") as f: c = f.read()
c = c.replace('e: any =>', '(e: any) =>')
with open(file, "w", encoding="utf-8") as f: f.write(c)

print("TS Syntax fixed.")