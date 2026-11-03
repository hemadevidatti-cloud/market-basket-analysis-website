from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import io, os
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def sample_transactions():
    return [
        ["Bread","Milk","Butter"], ["Bread","Milk"], ["Bread","Butter"],
        ["Milk","Butter"], ["Bread","Milk","Eggs"], ["Bread","Eggs"],
        ["Milk","Eggs"], ["Bread","Milk","Butter"], ["Coffee","Bread"],
        ["Coffee","Milk"], ["Coffee","Bread","Milk"], ["Eggs","Butter"],
        ["Bread","Milk"], ["Bread","Butter","Eggs"], ["Coffee","Milk","Butter"],
        ["Bread","Milk","Eggs"], ["Coffee","Bread"], ["Milk","Butter","Eggs"],
        ["Bread","Milk","Butter"], ["Coffee","Bread","Butter"]
    ]

def read_transactions(file_storage=None):
    """Read either TransactionID/Item rows or one basket per row."""
    if not file_storage or not file_storage.filename:
        return sample_transactions()
    try:
        df = pd.read_csv(file_storage)
    except Exception as exc:
        raise ValueError(f"Could not read this CSV file: {exc}")
    if df.empty or len(df.columns) == 0:
        raise ValueError("The CSV file is empty. Add transaction data and try again.")
    df.columns = [str(c).strip().lower() for c in df.columns]
    id_names = ["transactionid", "transaction_id", "order_id", "basket_id", "transaction id", "order id", "basket id"]
    id_col = next((c for c in id_names if c in df.columns), None)
    if "item" in df.columns and id_col:
        clean = df.dropna(subset=["item", id_col]).copy()
        clean["item"] = clean["item"].astype(str).str.strip()
        clean = clean[(clean["item"] != "") & (clean["item"].str.lower() != "nan")]
        transactions = clean.groupby(id_col, sort=False)["item"].apply(list).tolist()
    else:
        ignored = set(id_names)
        item_columns = [c for c in df.columns if c not in ignored]
        if not item_columns:
            raise ValueError("CSV needs an Item column plus a transaction ID, or one row per basket with product columns.")
        transactions = []
        for _, row in df[item_columns].iterrows():
            items = [str(v).strip() for v in row.tolist()
                     if pd.notna(v) and str(v).strip() and str(v).strip().lower() != "nan"]
            if items:
                transactions.append(items)
    if not transactions:
        raise ValueError("No usable transactions found. Check that your CSV contains transaction IDs and product names.")
    return transactions

def analyze(transactions, min_support=0.1, min_confidence=0.3, algorithm="apriori"):
    transactions = [list(dict.fromkeys([str(x).strip() for x in t if str(x).strip()])) for t in transactions]
    transactions = [t for t in transactions if t]
    if not transactions:
        raise ValueError("No usable transactions were found in the CSV.")
    te = TransactionEncoder()
    encoded = te.fit(transactions).transform(transactions)
    basket = pd.DataFrame(encoded, columns=te.columns_)
    fn = fpgrowth if algorithm == "fpgrowth" else apriori
    itemsets = fn(basket, min_support=min_support, use_colnames=True)
    if itemsets.empty:
        rules = pd.DataFrame()
    else:
        try:
            rules = association_rules(itemsets, metric="confidence", min_threshold=min_confidence)
        except (ValueError, KeyError):
            rules = pd.DataFrame()
    itemsets = itemsets.sort_values("support", ascending=False).copy()
    if not itemsets.empty:
        itemsets["items"] = itemsets["itemsets"].apply(lambda s: " + ".join(sorted(s)))
        itemsets["count"] = (itemsets["support"] * len(transactions)).round().astype(int)
    if not rules.empty:
        rules = rules.sort_values(["lift","confidence"], ascending=False).copy()
        rules["antecedents_text"] = rules["antecedents"].apply(lambda s: " + ".join(sorted(s)))
        rules["consequents_text"] = rules["consequents"].apply(lambda s: " + ".join(sorted(s)))
        rules["rule"] = rules["antecedents_text"] + " → " + rules["consequents_text"]
    return transactions, itemsets, rules, len(set(x for t in transactions for x in t))

@app.route("/", methods=["GET","POST"])
def index():
    result = None
    uploaded_filename = None
    if request.method == "POST":
        try:
            support = float(request.form.get("min_support", "0.1"))
            confidence = float(request.form.get("min_confidence", "0.3"))
            algorithm = request.form.get("algorithm", "apriori").lower()
            if algorithm not in ("apriori", "fpgrowth"):
                raise ValueError("Choose either Apriori or FP-Growth.")
            if not 0 < support <= 1 or not 0 <= confidence <= 1:
                raise ValueError("Support must be greater than 0 and at most 1. Confidence must be from 0 to 1.")
            upload = request.files.get("csv_file")
            uploaded_filename = upload.filename if upload and upload.filename else None
            tx = read_transactions(upload if uploaded_filename else None)
            tx, itemsets, rules, product_count = analyze(tx, support, confidence, algorithm)
            result = {
                "transactions": len(tx), "products": product_count,
                "itemsets": itemsets.head(100).to_dict("records"),
                "itemset_total": len(itemsets),
                "rules": rules.head(100).to_dict("records") if not rules.empty else [],
                "rule_total": len(rules),
                "top_items": [{"label": r["items"], "support": round(float(r["support"]),3)} for _,r in itemsets.head(8).iterrows()],
                "top_rules": [{"label": r["rule"], "lift": round(float(r["lift"]),3)} for _,r in rules.head(8).iterrows()] if not rules.empty else [],
                "algorithm": algorithm.upper()
            }
            # Convert sets to simple display strings already prepared above.
            for row in result["itemsets"]:
                row["support"] = round(float(row["support"]), 3)
            for row in result["rules"]:
                for key in ["support","confidence","lift","leverage","conviction"]:
                    if key in row and pd.notna(row[key]) and row[key] != float("inf"):
                        row[key] = round(float(row[key]),3)
                    elif key in row:
                        row[key] = "∞" if row[key] == float("inf") else "—"
            result["insights"] = make_insights(result["itemsets"], result["rules"])
        except Exception as e:
            flash(str(e), "error")
    return render_template("index.html", result=result, uploaded_filename=uploaded_filename)

def make_insights(itemsets, rules):
    insights=[]
    if itemsets:
        top=itemsets[0]
        insights.append(f"Most frequent combination: {top['items']} appears in about {top['support']*100:.1f}% of baskets. Consider displaying these products together.")
    if rules:
        best=rules[0]
        if isinstance(best.get("lift"), (int,float)) and best["lift"] > 1:
            insights.append(f"Cross-sell opportunity: customers buying {best['antecedents_text']} are more likely to buy {best['consequents_text']} too (lift {best['lift']:.2f}). Test a bundle or checkout recommendation.")
        strong=max(rules, key=lambda r: float(r.get("confidence",0) or 0))
        insights.append(f"High-confidence rule: {strong['antecedents_text']} → {strong['consequents_text']} has confidence {float(strong['confidence'])*100:.1f}%. Place the suggested item near the trigger product.")
    if not insights:
        insights.append("No association rules met the current thresholds. Lower minimum support or confidence and run the analysis again.")
    insights.append("Use these patterns as experiments: compare click-through, basket size, and margin before making permanent merchandising changes.")
    return insights

@app.route("/download-sample")
def download_sample():
    csv_text = "TransactionID,Item\n" + "\n".join(f"{i},{item}" for i,t in enumerate(sample_transactions(),1) for item in t)
    return send_file(io.BytesIO(csv_text.encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name="sample_transactions.csv")

if __name__ == "__main__":
    app.run(debug=True)
