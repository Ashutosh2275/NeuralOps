import os
import re

# Fix Dashboard.tsx
file = "frontend/src/pages/Dashboard.tsx"
with open(file, "r", encoding="utf-8") as f:
    c = f.read()

c = re.sub(r'import { useWebSocket } from "../hooks/useWebSocket";\n', '', c)
c = re.sub(r'const { events } = useWebSocket\(\);\n', '', c)
c = c.replace('wsEvents={events}', 'wsEvents={[]}')

with open(file, "w", encoding="utf-8") as f:
    f.write(c)

# Fix IncidentDetail.tsx
file = "frontend/src/pages/IncidentDetail.tsx"
with open(file, "r", encoding="utf-8") as f:
    c = f.read()

c = re.sub(r'import { useWebSocket } from "../hooks/useWebSocket";\n', '', c)
c = re.sub(r'const { events } = useWebSocket\(\);\n', '', c)

with open(file, "w", encoding="utf-8") as f:
    f.write(c)

# Fix SecurityResilience.tsx
file = "frontend/src/pages/SecurityResilience.tsx"
with open(file, "r", encoding="utf-8") as f:
    c = f.read()

c = re.sub(r'import { useWebSocket } from "../hooks/useWebSocket";\n', '', c)
c = re.sub(r'const { connected, events } = useWebSocket\(\);\n', 'const connected = true; const events: any[] = [];\n', c)

with open(file, "w", encoding="utf-8") as f:
    f.write(c)

# Fix AIInsightsPanel.tsx
file = "frontend/src/components/dashboard/AIInsightsPanel.tsx"
with open(file, "r", encoding="utf-8") as f:
    c = f.read()

c = re.sub(r'import type { WSEvent } from "../../hooks/useWebSocket";\n', '', c)
c = c.replace('wsEvents: WSEvent[];', 'wsEvents?: any[];')
c = c.replace('wsEvents:', 'wsEvents = [],')

with open(file, "w", encoding="utf-8") as f:
    f.write(c)

# Fix AIAssistantPanel.tsx
file = "frontend/src/components/dashboard/AIAssistantPanel.tsx"
with open(file, "r", encoding="utf-8") as f:
    c = f.read()

c = re.sub(r'import type { WSEvent } from "../../hooks/useWebSocket";\n', '', c)
c = c.replace('events: WSEvent[];', 'events?: any[];')

with open(file, "w", encoding="utf-8") as f:
    f.write(c)

print("Files fixed successfully!")
