import pandas as pd

# Final dosyanı oku
df = pd.read_csv('training_data.csv')

# Kategorilerin (Label) dağılımını gör
print("--- Kategori Dağılımı ---")
print(df['label'].value_counts())

# Yüzdesel oranları gör
print("\n--- Yüzdesel Dağılım ---")
print(df['label'].value_counts(normalize=True) * 100)

