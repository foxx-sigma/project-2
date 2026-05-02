# ============================================================
# FINAL PRAKTIKUM ANALISIS DATA (AUTO-ADAPT DATASET)
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from scipy import stats

# ============================================================
# 1. LOAD DATA
# ============================================================
df = pd.read_csv("data_praktikum_analisis.csv")

print("Kolom awal:", df.columns.tolist())

# ============================================================
# 2. AUTO RENAME (BIAR FLEXIBLE)
# ============================================================
rename_map = {
    "Order_Date": "Date",
    "order_date": "Date",
    "Customer_Id": "CustomerID",
    "customer_id": "CustomerID",
    "Quantity": "Qty",
    "quantity": "Qty",
    "Total_Sales": "Amount",
    "total_sales": "Amount",
    "Product_Category": "Category",
}

df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

# fallback kalau CustomerID tidak ada
if "CustomerID" not in df.columns:
    df["CustomerID"] = df.index

# fallback kalau Ad_Budget tidak ada
if "Ad_Budget" not in df.columns:
    df["Ad_Budget"] = df["Amount"] * 0.2

# ============================================================
# 3. DATA CLEANING
# ============================================================
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Amount", "Qty", "Date"])
df = df[(df["Amount"] > 0) & (df["Qty"] > 0)]

df["Price_Per_Unit"] = df["Amount"] / df["Qty"]
df["Month"] = df["Date"].dt.to_period("M").astype(str)

print("Data siap:", df.shape)

# ============================================================
# 4. TREN BULANAN
# ============================================================
monthly = df.groupby("Month")["Amount"].sum()

plt.figure()
plt.plot(monthly.index, monthly.values, marker="o")
plt.title("Tren Penjualan Bulanan")
plt.xticks(rotation=45)
plt.savefig("01_tren.png")
plt.close()

# ============================================================
# 5. KORELASI
# ============================================================
sns.heatmap(df[["Amount","Qty","Price_Per_Unit"]].corr(), annot=True)
plt.title("Heatmap Korelasi")
plt.savefig("02_korelasi.png")
plt.close()

# ============================================================
# 6. TUGAS 1 — UNDERPERFORMER
# ============================================================
prod = df.groupby("Category").agg(
    Avg_Price=("Price_Per_Unit","mean"),
    Total_Qty=("Qty","sum")
).reset_index()

avg_price = prod["Avg_Price"].mean()
low_qty = prod["Total_Qty"].quantile(0.25)

under = prod[
    (prod["Avg_Price"] > avg_price) &
    (prod["Total_Qty"] < low_qty)
]

print("\nUNDERPERFORMER:\n", under)

plt.figure()
plt.scatter(prod["Avg_Price"], prod["Total_Qty"])
plt.axvline(avg_price, linestyle="--")
plt.title("Underperformer")
plt.savefig("03_underperformer.png")
plt.close()

# ============================================================
# 7. TUGAS 2 — RFM
# ============================================================
snapshot = df["Date"].max() + dt.timedelta(days=1)

rfm = df.groupby("CustomerID").agg(
    Recency=("Date", lambda x: (snapshot - x.max()).days),
    Frequency=("CustomerID","count"),
    Monetary=("Amount","sum")
)

rfm["Score"] = (
    pd.qcut(rfm["Recency"],5,labels=[5,4,3,2,1]).astype(int) +
    pd.qcut(rfm["Frequency"].rank(method="first"),5,labels=[1,2,3,4,5]).astype(int) +
    pd.qcut(rfm["Monetary"],5,labels=[1,2,3,4,5]).astype(int)
)

print("\nTOP CUSTOMER:\n", rfm.sort_values("Score", ascending=False).head())

# ============================================================
# 8. TUGAS 3 — EFISIENSI
# ============================================================
cat = df.groupby("Category").agg(
    Revenue=("Amount","sum"),
    Ad_Budget=("Ad_Budget","sum")
).reset_index()

cat["Efficiency"] = cat["Revenue"] / cat["Ad_Budget"]
cat = cat.sort_values("Efficiency")

print("\nEFISIENSI:\n", cat)

plt.figure()
plt.barh(cat["Category"], cat["Efficiency"])
plt.title("Efisiensi Kategori")
plt.savefig("04_efisiensi.png")
plt.close()

# ============================================================
# 9. TUGAS 4 — HIPOTESIS
# ============================================================
median_ads = df["Ad_Budget"].median()

high = df[df["Ad_Budget"] > median_ads]["Amount"]
low  = df[df["Ad_Budget"] <= median_ads]["Amount"]

t, p = stats.ttest_ind(high, low)

print("\nUJI HIPOTESIS p-value:", p)

# ============================================================
# 10. REGRESI
# ============================================================
X = df[["Ad_Budget"]]
y = df["Amount"]

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

r2 = model.score(X_test, y_test)

print("\nREGRESI R2:", r2)

# ============================================================
# 11. KESIMPULAN
# ============================================================
best = cat.iloc[-1]["Category"]
worst = cat.iloc[0]["Category"]

print(f"""
KESIMPULAN:
- Kategori terbaik: {best}
- Kategori terburuk: {worst}
- p-value: {p:.4f}
- R2 model: {r2:.2f}
""")