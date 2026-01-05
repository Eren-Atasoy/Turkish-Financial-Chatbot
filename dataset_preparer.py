import pandas as pd
import os

# Dosya listesi ve her birine atanacak kısa etiketler
dosya_plani = {
    'ready_for_training_thyao.csv': 'THY',
    'ready_for_training_akbank.csv': 'AKBNK',
    'ready_for_training_bist100.csv': 'BIST100',
    'ready_for_training_usdtry.csv': 'USDTRY',
    'ready_for_training_garan.csv': 'GARAN',
    'ready_for_training_eregl.csv': 'EREGL',
    'ready_for_training_kchol.csv': 'KCHOL',
    'ready_for_training_gold.csv': 'ALTIN',
    'ready_for_training_silver.csv': 'GUMUS'
}

birlesmis_liste = []

print("[*] Veriler birleştiriliyor ve hisse kimlikleri (prefix) ekleniyor...")

for dosya, etiket in dosya_plani.items():
    if os.path.exists(dosya):
        # Dosyayı oku
        temp_df = pd.read_csv(dosya)
        
        # 'text' sütununun başına [ETIKET] ekle
        # Örn: [GARAN] 12 Mart 200 lira sonrasına...
        temp_df['text'] = temp_df['text'].apply(lambda x: f"[{etiket}] {str(x)}")
        
        birlesmis_liste.append(temp_df)
        print(f"[+] {etiket} eklendi: {len(temp_df)} satır.")
    else:
        print(f"[!] Uyarı: {dosya} bulunamadı, bu adım atlanıyor.")

# Tüm verileri tek bir tabloda topla
final_dataset = pd.concat(birlesmis_liste, ignore_index=True)

# Veriyi Karıştır (Shuffle)
# BERT modelinin hep aynı hisseyi üst üste görmemesi için karıştırmak çok önemlidir
final_dataset = final_dataset.sample(frac=1).reset_index(drop=True)

# Final dosyasını kaydet
final_dataset.to_csv('ANA_VERI_SETI.csv', index=False, encoding='utf-8-sig')

print(f"\n[BAŞARILI] Toplam {len(final_dataset)} satırlık veri 'ANA_VERI_SETI.csv' adıyla hazır!")