import pandas as pd
from zemberek import TurkishMorphology, TurkishSentenceNormalizer
import os
import re

# 1. Zemberek Modellerini Başlatma
print("[*] Zemberek modelleri yükleniyor (Lütfen bekleyin)...")
try:
    morphology = TurkishMorphology.create_with_defaults()
    normalizer = TurkishSentenceNormalizer(morphology)
    print("[+] Zemberek başarıyla yüklendi.")
except Exception as e:
    print(f"[!] Zemberek yüklenirken hata oluştu: {e}")
    exit()

def nlp_islem_yap(metin):
    if not isinstance(metin, str) or metin.strip() == "":
        return ""
    
    try:
        # Etiketi (Örn: [THY]) korumak için ayırıyoruz
        match = re.match(r"(\[.*?\])\s*(.*)", metin)
        if match:
            etiket = match.group(1)
            yorum = match.group(2)
        else:
            etiket = ""
            yorum = metin

        # A. Normalizasyon (Yazım hataları ve kısaltmalar)
        # Örn: "alsakmi" -> "alsak mı"
        normalize_edilmis = normalizer.normalize(yorum)
        
        # B. Kök Bulma (Lemmatization)
        # Örn: "hisselerimizden" -> "hisse"
        analiz = morphology.analyze_sentence(normalize_edilmis)
        sonuclar = morphology.disambiguate(normalize_edilmis, analiz).best_analysis()
        
        kokler = [res.item.lemma for res in sonuclar if res.item.lemma != "UNK"] # Bilinmeyenleri at
        temiz_metin = " ".join(kokler)

        # Etiketi geri birleştiriyoruz
        return f"{etiket} {temiz_metin}".strip()
    
    except:
        return metin # Hata durumunda orijinal metni döndür

# 2. ANA_VERI_SETI.csv Dosyasını İşleme
input_file = 'ANA_VERI_SETI.csv'
output_file = 'final_data_for_training.csv'

if os.path.exists(input_file):
    df = pd.read_csv(input_file)
    print(f"[*] {len(df)} satır üzerinde NLP işlemleri başlıyor. Bu işlem biraz sürebilir...")
    
    # NLP fonksiyonunu tüm satırlara uygula
    df['text'] = df['text'].apply(nlp_islem_yap)
    
    # Temizlenmiş veriyi kaydet
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n[BAŞARILI] İşlem bitti!")
    print(f"[*] Final Dosyası: {output_file}")
    print(f"[*] Örnek Metin: {df['text'].iloc[0]}")
else:
    print(f"[!] Hata: {input_file} dosyası bulunamadı!")