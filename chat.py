"""
Finansal Chatbot - Inference Script
====================================
Bu script, eğitilmiş BERT modelini kullanarak kullanıcı sorularını sınıflandırır.
"""

import torch
import random
import re
from transformers import BertTokenizer, BertForSequenceClassification

# Canlı fiyat verisi için
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("[!] yfinance yüklü değil. Gerçek fiyat özelliği devre dışı.")

# Zemberek yükleme (sadece normalizasyon için)
print("[*] Model yükleniyor...")
try:
    from zemberek import TurkishMorphology, TurkishSentenceNormalizer
    morphology = TurkishMorphology.create_with_defaults()
    normalizer = TurkishSentenceNormalizer(morphology)
    ZEMBEREK_AVAILABLE = True
    print("[+] Zemberek yüklendi.")
except:
    ZEMBEREK_AVAILABLE = False
    print("[!] Zemberek bulunamadı, temel temizlik kullanılacak.")

# Model yükleme
model_path = "./finans_model"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path)
model.eval()
print("[+] Model yüklendi.")

# Etiket isimleri (train_bert.py ile aynı sırada olmalı)
label_names = [
    'Genel Bilgi/Durum',
    'Risk ve Haber Analizi', 
    'Hedef Fiyat Sorgulama',
    'Alım-Satım Niyeti',
    'Piyasa Trend/Tahmin'
]

# Varlık sözlüğü (NER)
ner_sozlugu = {
    "akbank": "AKBNK", "akbnk": "AKBNK",
    "thy": "THY", "türk hava yolları": "THY", "thyao": "THY",
    "garan": "GARAN", "garanti": "GARAN",
    "eregl": "EREGL", "ereğli": "EREGL",
    "kchol": "KCHOL", "koç": "KCHOL", "koc": "KCHOL",
    "dolar": "DOLAR", "usd": "DOLAR", "usdtry": "DOLAR",
    "euro": "EURO", "eur": "EURO",
    "altın": "ALTIN", "altin": "ALTIN", "gold": "ALTIN", "ons": "ALTIN",
    "gümüş": "GUMUS", "gumus": "GUMUS", "silver": "GUMUS",
    "bist": "BIST100", "bist100": "BIST100", "endeks": "BIST100", "borsa": "BIST100"
}

# =============================================================================
# CANLI FİYAT VERİSİ (yfinance)
# =============================================================================

# Yahoo Finance ticker eşleştirmesi
TICKER_MAP = {
    "THY": "THYAO.IS",       # Türk Hava Yolları
    "GARAN": "GARAN.IS",     # Garanti Bankası
    "AKBNK": "AKBNK.IS",     # Akbank
    "EREGL": "EREGLI.IS",    # Ereğli Demir Çelik
    "KCHOL": "KCHOL.IS",     # Koç Holding
    "DOLAR": "USDTRY=X",     # USD/TRY kuru
    "EURO": "EURTRY=X",      # EUR/TRY kuru
    "ALTIN": "GC=F",         # Altın (USD/ons)
    "GUMUS": "SI=F",         # Gümüş (USD/ons)
    "BIST100": "XU100.IS"    # BIST 100 Endeksi
}

# Para birimi eşleştirmesi (görüntüleme için)
PARA_BIRIMI = {
    "THY": "TL", "GARAN": "TL", "AKBNK": "TL", "EREGL": "TL", "KCHOL": "TL",
    "DOLAR": "TL", "EURO": "TL", "BIST100": "puan",
    "ALTIN": "USD", "GUMUS": "USD"
}

# Fiyat cache'i (rate limit hatalarını önlemek için)
# Yapısı: {"THY": {"fiyat": 284.5, "zaman": timestamp}}
fiyat_cache = {}
CACHE_SURESI = 300  # 5 dakika (saniye cinsinden)


def gercek_fiyat_al(varlik_kodu):
    """
    Yahoo Finance API'den gerçek zamanlı fiyat çeker.
    
    Rate limit'i önlemek için:
    - history() metodu kullanır (daha stabil)
    - 10 dakikalık cache
    - Retry logic
    
    Parametreler:
        varlik_kodu: İç varlık kodu (örn: "THY", "DOLAR")
    
    Döndürür:
        float: Güncel fiyat veya None (hata durumunda)
    """
    import time
    import logging
    
    # yfinance loglarını sustur (429 hatalarını gizle)
    logging.getLogger('yfinance').setLevel(logging.CRITICAL)
    
    if not YFINANCE_AVAILABLE:
        return None
    
    ticker_sembolu = TICKER_MAP.get(varlik_kodu)
    if not ticker_sembolu:
        return None
    
    # Cache kontrolü (10 dakika)
    if varlik_kodu in fiyat_cache:
        cache_veri = fiyat_cache[varlik_kodu]
        gecen_sure = time.time() - cache_veri["zaman"]
        if gecen_sure < CACHE_SURESI:
            print(f"[*] Cache'den fiyat alındı: {varlik_kodu} ({int(CACHE_SURESI - gecen_sure)}s kaldı)")
            return cache_veri["fiyat"]
    
    # Retry logic ile API çağrısı
    max_deneme = 2
    for deneme in range(max_deneme):
        try:
            ticker = yf.Ticker(ticker_sembolu)
            
            # history() metodu daha güvenilir
            hist = ticker.history(period="5d")
            
            if hist.empty:
                if deneme < max_deneme - 1:
                    print(f"[*] Tekrar deneniyor... ({deneme + 1}/{max_deneme})")
                    time.sleep(2)  # 2 saniye bekle
                    continue
                print(f"[!] Veri bulunamadı: {varlik_kodu}")
                if varlik_kodu in fiyat_cache:
                    return fiyat_cache[varlik_kodu]["fiyat"]
                return None
            
            # Son kapanış fiyatını al
            fiyat = float(hist['Close'].iloc[-1])
            
            # Cache'e kaydet
            fiyat_cache[varlik_kodu] = {
                "fiyat": fiyat,
                "zaman": time.time()
            }
            print(f"[+] API'den fiyat alındı: {varlik_kodu} = {fiyat:.2f}")
            
            return fiyat
            
        except Exception as e:
            if deneme < max_deneme - 1:
                print(f"[*] Hata, tekrar deneniyor... ({deneme + 1}/{max_deneme})")
                time.sleep(2)
                continue
            print(f"[!] Fiyat alınamadı ({varlik_kodu}): {type(e).__name__}")
            if varlik_kodu in fiyat_cache:
                print(f"[*] Eski cache kullanılıyor: {varlik_kodu}")
                return fiyat_cache[varlik_kodu]["fiyat"]
            return None
    
    return None


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def metin_temizle(text):
    """Metni model için hazırla (preprocessing ile aynı)"""
    if ZEMBEREK_AVAILABLE:
        try:
            text = normalizer.normalize(text)
        except:
            pass
    
    # Temel temizlik
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'@\w+|#\w+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def varlik_bul(text):
    """Metinden finansal varlık tespit et"""
    text_lower = text.lower()
    for anahtar, varlik in ner_sozlugu.items():
        if anahtar in text_lower:
            return varlik
    return None


def tahmin_yap(text):
    """Model ile niyet tahmini yap"""
    # Metni temizle
    temiz_text = metin_temizle(text)
    
    # Tokenize ve tahmin
    inputs = tokenizer(
        temiz_text, 
        return_tensors="pt", 
        truncation=True, 
        padding=True, 
        max_length=128
    )
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        pred_idx = torch.argmax(probs).item()
        guven = probs[0][pred_idx].item()
    
    return label_names[pred_idx], guven


# =============================================================================
# DİYALOG HAFIZASI (Context Memory)
# =============================================================================

class KonusmaHafizasi:
    """
    Kullanıcı ile konuşma bağlamını tutar.
    
    Özellikler:
        - Son konuşulan varlığı hatırlar
        - Son tahmin edilen niyeti saklar
        - Son 5 soru-cevap çiftini tutar
        - Referans sorularını ("Peki?", "Ya o?") çözer
    """
    
    def __init__(self):
        self.son_varlik = None      # Son konuşulan varlık kodu
        self.son_niyet = None       # Son tahmin edilen niyet
        self.gecmis = []            # [(soru, cevap), ...] - Son 5 tur
    
    def guncelle(self, varlik, niyet, soru, cevap):
        """Hafızayı yeni konuşma ile güncelle"""
        if varlik:
            self.son_varlik = varlik
        if niyet:
            self.son_niyet = niyet
        
        self.gecmis.append((soru, cevap))
        # Maksimum 5 tur tut
        if len(self.gecmis) > 5:
            self.gecmis.pop(0)
    
    def referans_var_mi(self, soru):
        """
        Soru bir referans içeriyor mu kontrol et.
        Örnek: "Peki Garanti?" → son niyeti kullan
        """
        referans_kelimeler = ["peki", "ya", "onun", "bu", "o da", "aynısı", "öyle mi"]
        soru_lower = soru.lower()
        return any(kelime in soru_lower for kelime in referans_kelimeler)
    
    def sifirla(self):
        """Hafızayı temizle"""
        self.son_varlik = None
        self.son_niyet = None
        self.gecmis = []


# Global hafıza nesnesi
hafiza = KonusmaHafizasi()


# =============================================================================
# ETİKET BAZLI RESPONSE STRATEJİLERİ
# =============================================================================

def cevap_genel_bilgi(varlik, soru):
    """
    Genel Bilgi/Durum için response stratejisi.
    Fiyat bilgisi GÖSTERME - sadece genel bilgi ver.
    """
    sablonlar = [
        f"{varlik} şu an piyasada aktif olarak işlem görüyor.",
        f"{varlik} ile ilgili genel piyasa durumu stabil seyrediyor.",
        f"{varlik} hakkında güncel gelişmeleri takip etmenizi öneririm.",
        f"{varlik} piyasasında normal işlem akışı devam ediyor.",
    ]
    return random.choice(sablonlar)


def cevap_risk_analizi(varlik, soru):
    """
    Risk ve Haber Analizi için response stratejisi.
    Risk faktörlerini ve haber takibini vurgula.
    """
    # Soru içinde risk kelimeleri var mı kontrol et
    risk_kelimeleri = ["risk", "tehlike", "düşüş", "kriz", "zarar"]
    haber_kelimeleri = ["haber", "gelişme", "açıklama", "duyuru"]
    
    soru_lower = soru.lower()
    
    if any(k in soru_lower for k in risk_kelimeleri):
        sablonlar = [
            f"{varlik} için risk değerlendirmesi yaparken makroekonomik faktörleri göz önünde bulundurun.",
            f"{varlik} yatırımlarında risk yönetimi için portföy çeşitlendirmesi önemlidir.",
            f"{varlik} ile ilgili risk faktörleri sektörel gelişmelere bağlı olarak değişkenlik gösterebilir.",
        ]
    elif any(k in soru_lower for k in haber_kelimeleri):
        sablonlar = [
            f"{varlik} hakkında güncel haberleri finansal haber kaynaklarından takip edebilirsiniz.",
            f"{varlik} ile ilgili son gelişmeler için KAP (Kamuyu Aydınlatma Platformu) bildirilerini inceleyin.",
            f"{varlik} haberlerini takip etmek için finansal analiz platformlarını kullanmanızı öneririm.",
        ]
    else:
        sablonlar = [
            f"{varlik} için risk ve haber analizini düzenli takip etmenizi öneririm.",
            f"{varlik} yatırım kararlarında haber akışı ve risk faktörlerini değerlendirin.",
        ]
    
    return random.choice(sablonlar)


def cevap_fiyat_sorgulama(varlik, soru):
    """
    Hedef Fiyat Sorgulama için response stratejisi.
    SADECE BU ETİKETTE fiyat bilgisi göster!
    """
    # Gerçek fiyat al
    gercek_fiyat = gercek_fiyat_al(varlik)
    para_birimi = PARA_BIRIMI.get(varlik, "TL")
    
    if gercek_fiyat:
        fiyat_str = f"{gercek_fiyat:,.2f} {para_birimi}"
        sablonlar = [
            f"{varlik} anlık fiyat: {fiyat_str}",
            f"{varlik} şu an {fiyat_str} seviyesinde işlem görüyor.",
            f"{varlik} güncel fiyatı: {fiyat_str}",
        ]
    else:
        sablonlar = [
            f"{varlik} için anlık fiyat bilgisi şu an alınamıyor. Lütfen daha sonra tekrar deneyin.",
            f"{varlik} fiyat verisi geçici olarak erişilemiyor. Piyasa saatlerinde tekrar kontrol edin.",
        ]
    
    return random.choice(sablonlar)


def cevap_alim_satim(varlik, soru):
    """
    Alım-Satım Niyeti için response stratejisi.
    Yatırım tavsiyesi vermeden, genel bilgi ve uyarı ver.
    """
    # Alım mı satım mı?
    soru_lower = soru.lower()
    alim_kelimeleri = ["alayım", "alsam", "almalı", "almak", "girsem", "girmeli"]
    satim_kelimeleri = ["satsam", "satayım", "satalım", "satmalı", "çıksam"]
    
    if any(k in soru_lower for k in alim_kelimeleri):
        sablonlar = [
            f"{varlik} için alım kararı vermeden önce kendi risk toleransınızı değerlendirin.",
            f"{varlik} alımı düşünüyorsanız, teknik ve temel analiz yapmanızı öneririm.",
            f"{varlik} için yatırım kararı kişisel finansal durumunuza ve hedeflerinize bağlıdır.",
            f"⚠️ Bu bir yatırım tavsiyesi değildir. {varlik} alım kararınızı kendi araştırmanıza dayandırın.",
        ]
    elif any(k in soru_lower for k in satim_kelimeleri):
        sablonlar = [
            f"{varlik} satış kararı için mevcut pozisyonunuzu ve hedeflerinizi gözden geçirin.",
            f"{varlik} satışı düşünüyorsanız, zarar kes/kar al seviyelerinizi belirlemiş olun.",
            f"⚠️ {varlik} satış kararınızı aceleci değil, stratejik verin.",
        ]
    else:
        sablonlar = [
            f"{varlik} alım-satım kararları kişisel risk toleransınıza bağlıdır.",
            f"{varlik} için işlem yapmadan önce piyasa koşullarını değerlendirin.",
            f"⚠️ Yatırım tavsiyesi değildir. {varlik} kararlarınızı kendi analizinize dayandırın.",
        ]
    
    return random.choice(sablonlar)


def cevap_trend_tahmin(varlik, soru):
    """
    Piyasa Trend/Tahmin için response stratejisi.
    Trend analizi ve genel piyasa yönü hakkında bilgi ver.
    """
    soru_lower = soru.lower()
    yukselis = ["yükselir", "çıkar", "artış", "yükseliş", "boğa"]
    dusus = ["düşer", "iner", "azalış", "düşüş", "ayı"]
    
    if any(k in soru_lower for k in yukselis):
        sablonlar = [
            f"{varlik} için yükseliş beklentisi teknik göstergelere ve piyasa koşullarına bağlıdır.",
            f"{varlik} yükseliş trendi için destek/direnç seviyelerini takip edin.",
            f"{varlik} artış potansiyeli sektörel ve makroekonomik faktörlere bağlı.",
        ]
    elif any(k in soru_lower for k in dusus):
        sablonlar = [
            f"{varlik} düşüş riski için stop-loss seviyelerinizi belirlemeniz önemli.",
            f"{varlik} düşüş trendinde dikkatli olun, kritik destek seviyelerini izleyin.",
        ]
    else:
        sablonlar = [
            f"{varlik} için orta vadeli trend takibi önemli, grafik analizi yapmanızı öneririm.",
            f"{varlik} trend analizi için hareketli ortalamalar ve hacim verilerini inceleyin.",
            f"{varlik} piyasa yönü için genel ekonomik göstergeleri takip edin.",
            f"{varlik} teknik analizinde trend çizgileri ve formasyonlara dikkat edin.",
        ]
    
    return random.choice(sablonlar)


# Response handler mapping
RESPONSE_HANDLERS = {
    'Genel Bilgi/Durum': cevap_genel_bilgi,
    'Risk ve Haber Analizi': cevap_risk_analizi,
    'Hedef Fiyat Sorgulama': cevap_fiyat_sorgulama,
    'Alım-Satım Niyeti': cevap_alim_satim,
    'Piyasa Trend/Tahmin': cevap_trend_tahmin,
}


def cevap_uret(soru):
    """
    Kullanıcı sorusuna akıllı cevap üret.
    
    Her etiket için özel response stratejisi kullanır:
    - Genel Bilgi: Piyasa durumu, fiyat YOK
    - Risk Analizi: Haber ve risk takibi
    - Fiyat Sorgulama: SADECE fiyat bilgisi
    - Alım-Satım: Uyarılar ve genel tavsiyeler
    - Trend/Tahmin: Teknik analiz bilgileri
    """
    global hafiza
    
    # 1. Varlık tespit et
    varlik = varlik_bul(soru)
    
    # 2. Eğer varlık bulunamadıysa, referans kontrolü yap
    if varlik is None:
        if hafiza.referans_var_mi(soru) and hafiza.son_varlik:
            varlik = hafiza.son_varlik
            print(f"[*] Hafızadan varlık alındı: {varlik}")
        else:
            return "Sorgunuzda bir finansal varlık (hisse, altın, dolar vb.) bulamadım. Lütfen belirtin."
    
    # 3. Niyet tahmin et
    if hafiza.referans_var_mi(soru) and hafiza.son_niyet:
        niyet = hafiza.son_niyet
        guven = 0.85
        print(f"[*] Hafızadan niyet alındı: {niyet}")
    else:
        niyet, guven = tahmin_yap(soru)
    
    # 4. Güven kontrolü
    if guven < 0.35:
        return f"{varlik} ile ilgili sorunuzu tam anlayamadım. Daha açık sorabilir misiniz?"
    
    # 5. Etiket bazlı response handler'ı çağır
    handler = RESPONSE_HANDLERS.get(niyet, cevap_genel_bilgi)
    cevap = handler(varlik, soru)
    
    # 6. Hafızayı güncelle
    sonuc = f"""
[Varlık]  : {varlik}
[Niyet]   : {niyet} (%{guven*100:.1f})
[Cevap]   : {cevap}
"""
    hafiza.guncelle(varlik, niyet, soru, sonuc)
    
    return sonuc


# Ana döngü
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  FİNANSAL CHATBOT")
    print("="*50)
    print("Çıkmak için 'exit' yazın.\n")
    
    while True:
        try:
            soru = input("Siz: ").strip()
            if soru.lower() == 'exit':
                print("Görüşmek üzere!")
                break
            if not soru:
                continue
            
            print("-" * 40)
            print(cevap_uret(soru))
            
        except KeyboardInterrupt:
            print("\nGörüşmek üzere!")
            break