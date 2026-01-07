"""
NLP Ön İşleme Modülü - Finansal Chatbot
========================================
Bu modül, Türkçe finansal yorumları temizler ve normalize eder.

Yapılan İşlemler:
1. URL ve mention temizleme
2. Noktalama normalizasyonu
3. Zemberek ile yazım düzeltme
4. Tekrarlayan karakterleri düzeltme
"""

import pandas as pd
import re
import os

# =============================================================================
# ZEMBEREK YÜKLEME
# =============================================================================
print("[*] Zemberek yükleniyor...")
try:
    from zemberek import TurkishMorphology, TurkishSentenceNormalizer
    morphology = TurkishMorphology.create_with_defaults()
    normalizer = TurkishSentenceNormalizer(morphology)
    ZEMBEREK_AVAILABLE = True
    print("[+] Zemberek başarıyla yüklendi.")
except Exception as e:
    print(f"[!] Zemberek yüklenemedi: {e}")
    ZEMBEREK_AVAILABLE = False

# =============================================================================
# TÜRKÇE STOP WORDS (Opsiyonel kullanım için)
# =============================================================================
TURKISH_STOP_WORDS = {
    've', 'veya', 'ama', 'için', 'ile', 'gibi', 'kadar',
    'ytd', 'bence', 'imo', ':)', ':(', ':D'
}

# =============================================================================
# TEMİZLİK FONKSİYONLARI
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
    """Çoklu noktalama işaretlerini tekile indirir"""
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    return text


def normalize_sayilar(text):
    """Türkçe sayı formatını düzeltir (1.234,56 -> 1234.56)"""
    text = re.sub(r'(\d)\.(\d{3})', r'\1\2', text)
    text = re.sub(r'(\d),(\d)', r'\1.\2', text)
    return text


def duzelt_tekrar(text):
    """Tekrarlayan harfleri düzeltir (çooook -> çook)"""
    return re.sub(r'(.)\1{2,}', r'\1\1', text)


def zemberek_duzelt(text):
    """Zemberek ile yazım hatalarını düzeltir"""
    if not ZEMBEREK_AVAILABLE:
        return text
    try:
        return normalizer.normalize(text)
    except:
        return text


def normalize_bosluk(text):
    """Fazla boşlukları temizler"""
    return re.sub(r'\s+', ' ', text).strip()


# =============================================================================
# ANA FONKSİYON
# =============================================================================

def temizle_stopwords(text):
    """Türkçe stop word'leri temizler"""
    words = text.split()
    words = [w for w in words if w.lower() not in TURKISH_STOP_WORDS]
    return ' '.join(words)


def nlp_islem_yap(text, zemberek_kullan=True, stopword_kaldir=True, min_uzunluk=10):
    """
    Metni temizler ve normalize eder.
    
    Parametreler:
    - text: İşlenecek metin
    - zemberek_kullan: Yazım düzeltme yapılsın mı?
    - min_uzunluk: Minimum karakter sayısı
    
    Döndürür:
    - Temizlenmiş metin (veya boş string)
    """
    if not isinstance(text, str) or text.strip() == "":
        return ""
    
    # 1. URL ve mention temizle
    text = temizle_url(text)
    text = temizle_mention(text)
    
    # 2. Sayı ve noktalama normalize et
    text = normalize_sayilar(text)
    text = normalize_noktalama(text)
    
    # 3. Tekrarlayan harfleri düzelt
    text = duzelt_tekrar(text)
    
    # 4. Zemberek ile yazım düzeltme
    if zemberek_kullan:
        text = zemberek_duzelt(text)
    
    # 5. Stop word temizle
    if stopword_kaldir:
        text = temizle_stopwords(text)
    
    # 6. Boşlukları normalize et
    text = normalize_bosluk(text)
    
    # 6. Uzunluk kontrolü
    if len(text) < min_uzunluk:
        return ""
    
    return text


# =============================================================================
# VERİ SETİ İŞLEME
# =============================================================================

def veri_seti_isle(girdi_dosya, cikti_dosya, metin_sutunu='text'):
    """
    CSV dosyasındaki tüm metinleri işler.
    
    Parametreler:
    - girdi_dosya: Okunacak CSV dosyası
    - cikti_dosya: Kaydedilecek CSV dosyası
    - metin_sutunu: Metin içeren sütun adı
    """
    if not os.path.exists(girdi_dosya):
        print(f"[!] Hata: {girdi_dosya} bulunamadı!")
        return None
    
    # Veriyi oku
    df = pd.read_csv(girdi_dosya)
    baslangic = len(df)
    print(f"[*] {baslangic} satır işleniyor...")
    
    # Temizlik uygula
    df[metin_sutunu] = df[metin_sutunu].apply(
        lambda x: nlp_islem_yap(x, zemberek_kullan=ZEMBEREK_AVAILABLE)
    )
    
    # Boş satırları sil
    df = df[df[metin_sutunu].str.len() > 10]
    bitis = len(df)
    
    print(f"[+] İşlem tamamlandı: {baslangic} -> {bitis} satır")
    
    # Kaydet
    df.to_csv(cikti_dosya, index=False, encoding='utf-8-sig')
    print(f"[+] Kaydedildi: {cikti_dosya}")
    
    return df


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  NLP Ön İşleme - Finansal Chatbot")
    print("=" * 50)
    
    # Dosya yolları
    GIRDI = 'training_data.csv'
    CIKTI = 'training_data_cleaned.csv'
    
    # İşle
    df = veri_seti_isle(GIRDI, CIKTI)
    
    if df is not None:
        print("\n[*] Örnek çıktılar:")
        for i, row in df.head(3).iterrows():
            print(f"  {row['text'][:60]}...")
        
        print("\n[*] Etiket dağılımı:")
        print(df['label'].value_counts())