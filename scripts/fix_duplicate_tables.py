import os
import re

models_dir = r"c:\Users\ASUS\Desktop\NetraAI\backend\src\sentinelops\models"
for filename in os.listdir(models_dir):
    if filename.endswith(".py"):
        filepath = os.path.join(models_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Replace occurrences of __tablename__ = "..." with __tablename__ = "..." \n    __table_args__ = {'extend_existing': True}
        # Only if __table_args__ is not already there
        
        lines = content.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            if "__tablename__" in line and "=" in line:
                # check if next line already has __table_args__
                if i + 1 < len(lines) and "__table_args__" in lines[i+1]:
                    continue
                # calculate indentation
                indent = len(line) - len(line.lstrip())
                new_lines.append(" " * indent + "__table_args__ = {'extend_existing': True}")
                
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(new_lines))
            
print("Fixed duplicate table registration issues.")
