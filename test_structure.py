import yfinance as yf

from strategy.structure import get_structure


df = yf.download(
    "GC=F",
    period="60d",
    interval="1h",
    auto_adjust=False,
    progress=False
)

if hasattr(df.columns, "levels"):
    df.columns = df.columns.get_level_values(0)

df = df.dropna()

result = get_structure(df)

print("\n========== TRADINGAI STRUCTURE ==========\n")

print("Structure :", result["structure"])
print("Swing High :", result["last_swing_high"])
print("Swing Low  :", result["last_swing_low"])
print("Last Swing :", result["last_swing_type"])
print("BOS        :", result["bos"])

print("\nDerniers swings :")

for swing in result["swings"][-10:]:
    print(swing)