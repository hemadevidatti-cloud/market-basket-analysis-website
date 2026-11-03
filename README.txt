MARKET BASKET ANALYSIS WEBSITE — BEGINNER SETUP (Windows)

WHAT IS INCLUDED
- app.py: Flask backend; reads CSV, runs Apriori or FP-Growth, calculates association rules, creates insights.
- templates/index.html: website frontend.
- static/style.css: responsive styling.
- requirements.txt: Python packages.
- sample CSV can be downloaded from inside the website.

STEP 1 — Extract the ZIP
Right-click market_basket_analysis_website.zip and choose Extract All.
Open the extracted market_basket_analysis_website folder in VS Code.

STEP 2 — Open a terminal in VS Code
Choose Terminal > New Terminal. Make sure the terminal is inside the folder containing app.py and requirements.txt.
Run: python --version
If that does not work on Windows, try: py --version

STEP 3 — Create a virtual environment (recommended)
Run: py -m venv .venv
Activate it in PowerShell:
.venv\Scripts\Activate.ps1
If you use Command Prompt instead:
.venv\Scripts\activate.bat
If activation is blocked, you can skip activation and use `py -m pip` in the next step.

STEP 4 — Install requirements
Run: py -m pip install -r requirements.txt
If `py` is not recognized but `python --version` works, use `python -m pip install -r requirements.txt`.

STEP 5 — Start the website
Run: py app.py
If needed, use: python app.py
Wait until Flask says it is running, then open this address in your browser:
http://127.0.0.1:5000

STEP 6 — Try it
Click “Analyze sample grocery data” to test the website.
To use your own data, click Choose a CSV file, select your CSV, choose Apriori or FP-Growth, set minimum support/confidence, and click Run analysis.

CSV FORMAT
Option A (recommended): two columns named TransactionID and Item. Each row is one product in a transaction.
Example:
TransactionID,Item
1001,Bread
1001,Milk
1002,Bread
1002,Eggs

Option B: one row per basket, each column containing an item. Example:
Item1,Item2,Item3
Bread,Milk,Butter
Bread,Eggs,
Coffee,Milk,

IMPORTANT
- The sample data is fictional and only demonstrates the workflow.
- Support = fraction of transactions containing an itemset.
- Confidence = how often the right-hand item appears when the left-hand item appears.
- Lift > 1 indicates a positive association compared with independent purchases.
- Treat recommendations as experiments; validate with real sales and margin data.
- For public deployment, disable Flask debug mode, set a strong secret key, and use a production WSGI server.

UPDATED NAVIGATION
The sidebar now works like separate pages. Clicking Dashboard, Upload Data, Frequent Itemsets, Association Rules, or Business Insights displays only that workspace section. It remains in the same local Flask website.

RESULT PAGE FIX
After uploading a CSV and clicking Run analysis, the website now automatically opens the Frequent Itemsets results page and displays an Analysis Complete banner. This avoids the confusing behavior where a form refresh returned the user to Dashboard and hid the analysis tables. Use the sidebar to move to Association Rules or Business Insights.

QUALITY AND DATA VALIDATION UPDATES
- Fixed Jinja dictionary display: itemset product names use row['items'] to avoid rendering Python's dict.items method.
- CSV input validates empty/unreadable files and supports TransactionID/Item long format and one-basket-per-row wide format.
- Algorithm choice is validated.
- Dashboard itemset/rule cards show full counts, while tables display up to 100 rows.
- Algorithm selection remains selected after analysis.
- Added clearer error styling and keyboard focus indicators.

CSV formats:
1) Long format: TransactionID,Item; one product per row, repeated transaction IDs group products into baskets.
2) Wide format: one basket per row, product values across each row.
