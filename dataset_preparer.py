import pandas as pd
import os

# Dosya listesi (Artık sadece birleştirme için kullanıyoruz)
dosyalar = [
    'ready_for_training_thyao.csv',
    'ready_for_training_akbank.csv',
    'ready_for_training_bist100.csv',
    'ready_for_training_usdtry.csv',
    'ready_for_training_garan.csv',
    'ready_for_training_eregl.csv',
    'ready_for_training_kchol.csv',
    'ready_for_training_gold.csv',
    'ready_for_training_silver.csv'
]

birlesmis_liste = []

print("[*] Veriler prefix (etiket) eklenmeden birleştiriliyor...")

for dosya in dosyalar:
    if os.path.exists(dosya):
        # Dosyayı oku
        temp_df = pd.read_csv(dosya)
        
        # Sadece text ve label sütunlarını aldığından emin olalım
        # Ve text sütununun string olduğundan emin olalım
        temp_df['text'] = temp_df['text'].astype(str)
        
        birlesmis_liste.append(temp_df)
        print(f"[+] {dosya} eklendi: {len(temp_df)} satır.")
    else:
        print(f"[!] Uyarı: {dosya} bulunamadı, bu adım atlanıyor.")

# Tüm verileri tek bir tabloda topla
final_dataset = pd.concat(birlesmis_liste, ignore_index=True)

# Veriyi Karıştır (Shuffle)
# Modelin öğrenme kalitesi için veriyi karıştırmak çok kritiktir
final_dataset = final_dataset.sample(frac=1, random_state=42).reset_index(drop=True)

# Final dosyasını kaydet
final_dataset.to_csv('combined_data.csv', index=False, encoding='utf-8-sig')

print(f"\n[BAŞARILI] Toplam {len(final_dataset)} satırlık veri 'combined_data.csv' adıyla hazır!")
print("[NOT] Köşeli parantez etiketleri kaldırıldı, model artık saf metinle eğitilecek.")