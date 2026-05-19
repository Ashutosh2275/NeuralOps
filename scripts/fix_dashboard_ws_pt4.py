import os

file = "frontend/src/components/dashboard/AIAssistantPanel.tsx"
with open(file, "r", encoding="utf-8") as f: c = f.read()
c = c.replace('const nplEvents = wsEvents.filter', 'const nplEvents = (wsEvents || []).filter')
with open(file, "w", encoding="utf-8") as f: f.write(c)

print("Fixed AIAssistantPanel.")