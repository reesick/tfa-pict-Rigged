import sqlite3
conn = sqlite3.connect('smartfinance.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cur.fetchall()
print("Tables in database:")
for t in tables:
    print(f"  ✓ {t[0]}")
print(f"\nTotal: {len(tables)} tables")
conn.close()
