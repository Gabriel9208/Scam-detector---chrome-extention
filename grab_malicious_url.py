import pandas as pd
import re
from pathlib import Path

file_path = Path(r"C:\Users\yen08\Desktop\scamDetector\Scam-detector---firefox-extention\phishing-list_1131210.xlsx")
df = pd.read_excel(file_path)

for index, row in df.iterrows():
    if row["狀態"] == "連結仍在線上":
        s = row["偽冒網址及行動應用程式下載位置"]
        s = re.sub(r'\[\.\]', '.', s)
        s = re.sub(r'hxxp', 'http', s)
        print(s)
