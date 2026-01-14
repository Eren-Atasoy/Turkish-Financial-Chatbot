"""
NLP On Isleme Modulu - Finansal Chatbot
========================================
Bu modul, Turkce finansal yorumlari temizler ve normalize eder.

Yapilan Islemler:
1. URL ve mention temizleme
2. Noktalama normalizasyonu
3. Zemberek ile yazim duzeltme
4. Tekrarlayan karakterleri duzeltme
"""

import pandas as pd
import re
import os

# =============================================================================
# ZEMBEREK YUKLEME
# =============================================================================
print("[*] Zemberek yukleniyor...")
try:
    from zemberek import TurkishMorphology, TurkishSentenceNormalizer
    morphology = TurkishMorphology.create_with_defaults()
    normalizer = TurkishSentenceNormalizer(morphology)
    ZEMBEREK_AVAILABLE = True
    print("[+] Zemberek basariyla yuklendi.")
except Exception as e:
    print(f"[!] Zemberek yuklenemedi: {e}")
    ZEMBEREK_AVAILABLE = False


# =============================================================================
# TEMIZLIK FONKSIYONLARI
# =============================================================================

def temizle_url(text):
    """URL'leri temizler"""
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    return text


def temizle_mention(text):
    """@mention ve #hashtag temizler"""
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    return text


def normalize_noktalama(text):
    """Coklu noktalama isaretlerini tekile indirir"""
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    return text


def normalize_sayilar(text):
    """Turkce sayi formatini duzeltir (1.234,56 -> 1234.56)"""
    text = re.sub(r'(\d)\.(\d{3})', r'\1\2', text)
    text = re.sub(r'(\d),(\d)', r'\1.\2', text)
    return text


def duzelt_tekrar(text):
    """Tekrarlayan harfleri duzeltir (cooook -> cook)"""
    return re.sub(r'(.)\1{2,}', r'\1\1', text)


def zemberek_duzelt(text):
    """Zemberek ile yazim hatalarini duzeltir"""
    if not ZEMBEREK_AVAILABLE:
        return text
    try:
        return normalizer.normalize(text)
    except:
        return text


def normalize_bosluk(text):
    """Fazla bosluklari temizler"""
    return re.sub(r'\s+', ' ', text).strip()


# =============================================================================
# ANA FONKSIYON
# =============================================================================

def nlp_islem_yap(text, zemberek_kullan=True, min_uzunluk=10):
    """
    Metni temizler ve normalize eder.
    
    Parametreler:
    - text: Islenecek metin
    - zemberek_kullan: Yazim duzeltme yapilsin mi?
    - min_uzunluk: Minimum karakter sayisi
    
    Dondurur:
    - Temizlenmis metin (veya bos string)
    """
    if not isinstance(text, str) or text.strip() == "":
        return ""
    
    # 1. URL ve mention temizle
    text = temizle_url(text)
    text = temizle_mention(text)
    
    # 2. Sayi ve noktalama normalize et
    text = normalize_sayilar(text)
    text = normalize_noktalama(text)
    
    # 3. Tekrarlayan harfleri duzelt
    text = duzelt_tekrar(text)
    
    # 4. Zemberek ile yazim duzeltme
    if zemberek_kullan:
        text = zemberek_duzelt(text)
    
    # 5. Bosluklari normalize et
    text = normalize_bosluk(text)
    
    # 6. Uzunluk kontrolu
    if len(text) < min_uzunluk:
        return ""
    
    return text


# =============================================================================
# VERI SETI ISLEME
# =============================================================================

def veri_seti_isle(girdi_dosya, cikti_dosya, metin_sutunu='text'):
    """
    CSV dosyasindaki tum metinleri isler.
    
    Parametreler:
    - girdi_dosya: Okunacak CSV dosyasi
    - cikti_dosya: Kaydedilecek CSV dosyasi
    - metin_sutunu: Metin iceren sutun adi
    """
    if not os.path.exists(girdi_dosya):
        print(f"[!] Hata: {girdi_dosya} bulunamadi!")
        return None
    
    # Veriyi oku
    df = pd.read_csv(girdi_dosya)
    baslangic = len(df)
    print(f"[*] {baslangic} satir isleniyor...")
    
    # Temizlik uygula
    df[metin_sutunu] = df[metin_sutunu].apply(
        lambda x: nlp_islem_yap(x, zemberek_kullan=ZEMBEREK_AVAILABLE)
    )
    
    # Bos satirlari sil
    df = df[df[metin_sutunu].str.len() > 10]
    bitis = len(df)
    
    print(f"[+] Islem tamamlandi: {baslangic} -> {bitis} satir")
    
    # Kaydet
    df.to_csv(cikti_dosya, index=False, encoding='utf-8-sig')
    print(f"[+] Kaydedildi: {cikti_dosya}")
    
    return df


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  NLP On Isleme - Finansal Chatbot")
    print("=" * 50)
    
    # Dosya yollari
    GIRDI = 'training_data.csv'
    CIKTI = 'training_data_cleaned.csv'
    
    # Isle
    df = veri_seti_isle(GIRDI, CIKTI)
    
    if df is not None:
        print("\n[*] Ornek ciktilar:")
        for i, row in df.head(3).iterrows():
            print(f"  {row['text'][:60]}...")
        
        print("\n[*] Etiket dagilimi:")
        print(df['label'].value_counts())