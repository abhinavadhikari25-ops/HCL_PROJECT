# VS Code mein project kaise kholen

1. `HRA-001_Hospital_Resource_Utilization_VSCode.zip` ko extract karein.
2. Extracted folder `HRA-001-Hospital-Resource-Utilization` ko open karein.
3. VS Code kholen → **File → Open Folder** → isi extracted folder ko select karein.
4. Terminal → New Terminal kholen.
5. Python 3.12 installed hona chahiye. Phir ye commands chalayein:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pip check
```

6. Tests check karne ke liye:

```powershell
python -m pytest -q
```

## Zaroori baat

Ye package Step 14 tak ke documents, database, synthetic data, source helpers aur tests ko ek jagah rakhta hai. Full Streamlit dashboard abhi develop nahi hua hai. `app.py`, cleaning/analysis modules aur 8 pages Step 15 ke BUILD tasks mein banenge. Isliye abhi `streamlit run app.py` chalana expected nahi hai.

Sabse pehle `BUILD_PLAN.md` padhein aur `STEP 15 — BUILD-01` se shuru karein.
