#!/usr/bin/env python3
"""
Create companies.xlsx with 10 bioplastic producers
"""

import pandas as pd
from pathlib import Path

# Paths
PROJECT_ROOT = Path('/home/sven/bioplastic-website-newsgenerator')
OUTPUT_FILE = PROJECT_ROOT / 'companies.xlsx'

# Create data with 10 bioplastic producers
companies_data = [
    {'Company': 'NatureWorks', 'Type': 'producer', 'Webpage': 'www.natureworksllc.com'},
    {'Company': 'BASF', 'Type': 'producer', 'Webpage': 'www.basf.com'},
    {'Company': 'Novamont', 'Type': 'producer', 'Webpage': 'www.novamont.com'},
    {'Company': 'Corbion', 'Type': 'producer', 'Webpage': 'www.corbion.com'},
    {'Company': 'Biome Bioplastics', 'Type': 'producer', 'Webpage': 'www.biomebioplastics.com'},
    {'Company': 'Danimer Scientific', 'Type': 'producer', 'Webpage': 'www.danimerscientific.com'},
    {'Company': 'Total Corbion PLA', 'Type': 'producer', 'Webpage': 'www.total-corbion.com'},
    {'Company': 'Mitsubishi Chemical', 'Type': 'producer', 'Webpage': 'www.mcgc.com'},
    {'Company': 'PTT MCC Biochem', 'Type': 'producer', 'Webpage': 'www.pttmcc.com'},
    {'Company': 'Futerro', 'Type': 'producer', 'Webpage': 'www.futerro.com'}
]

df = pd.DataFrame(companies_data)
df.to_excel(OUTPUT_FILE, index=False)

print(f"✅ Created {OUTPUT_FILE} with {len(df)} bioplastic producers")
