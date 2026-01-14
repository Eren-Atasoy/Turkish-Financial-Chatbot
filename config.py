"""
Finansal Chatbot - Konfigürasyon Dosyası
=========================================
API anahtarları ve sistem ayarları
"""

# =============================================================================
# API AYARLARI
# =============================================================================

# NewsAPI.org - Ücretsiz hesap: https://newsapi.org/register
# Günlük 100 istek hakkı var
NEWS_API_KEY = "a1634f7a437048aa990d03206116acb5"  # Buraya kendi API anahtarınızı girin

# DeepL API - Çeviri İçin (https://www.deepl.com/pro-api)
DEEPL_API_KEY = "3163134b-8654-4c18-8cb8-b90fb25c9748:fx"  # Buraya DeepL API Key gelecek


# =============================================================================
# MODEL AYARLARI
# =============================================================================

# BERT güven eşiği - bu değerin altındaki tahminler "anlayamadım" döner
GUVEN_ESIK = 0.35

# =============================================================================
# CACHE AYARLARI
# =============================================================================

# Fiyat cache süresi (saniye) - API rate limit'i önlemek için
CACHE_SURESI = 150  # 2.5 dakika

# Haber cache süresi (saniye) - aynı haberleri tekrar çekmemek için
HABER_CACHE_SURESI = 600  # 10 dakika

# =============================================================================
# VARLIK EŞLEŞTİRMELERİ
# =============================================================================

# Yahoo Finance ticker kodları
TICKER_MAP = {
    "THY": "THYAO.IS",
    "GARAN": "GARAN.IS",
    "AKBNK": "AKBNK.IS",
    "EREGL": "EREGLI.IS",
    "KCHOL": "KCHOL.IS",
    "DOLAR": "USDTRY=X",
    "EURO": "EURTRY=X",
    "ALTIN": "GC=F",
    "GUMUS": "SI=F",
    "BIST100": "XU100.IS"
}

# Para birimi eşleştirmesi
PARA_BIRIMI = {
    "THY": "TL", "GARAN": "TL", "AKBNK": "TL", "EREGL": "TL", "KCHOL": "TL",
    "DOLAR": "TL", "EURO": "TL", "BIST100": "puan",
    "ALTIN": "USD", "GUMUS": "USD"
}

# Haber araması için Google News RSS arama terimleri
HABER_ARAMA_MAP = {
    "THY": "THYAO hisse",
    "GARAN": "Garanti hisse",
    "AKBNK": "Akbank hisse",
    "EREGL": "Ereğli hisse",
    "KCHOL": "Koç Holding hisse",
    "DOLAR": "dolar kuru",
    "EURO": "euro kuru",
    "ALTIN": "altın fiyat",
    "GUMUS": "gümüş fiyat",
    "BIST100": "BIST borsa"
}

# TradingView News Flow URL'leri (fallback kaynak)
TRADINGVIEW_NEWS_MAP = {
    "THY": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=BIST:THYAO",
    "GARAN": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=BIST:GARAN",
    "AKBNK": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=BIST:AKBNK",
    "EREGL": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=BIST:EREGL",
    "KCHOL": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=BIST:KCHOL",
    "BIST100": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=BIST:XU100",
    "ALTIN": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=OANDA:XAUUSD",
    "GUMUS": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=OANDA:XAGUSD",
    "DOLAR": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=OANDA:USDTRY",
    "EURO": "https://tr.tradingview.com/news-flow/?provider=matriks,kap&symbol=OANDA:EURTRY"
}

# Türkçe varlık isimleri (görüntüleme için)
VARLIK_ISIM = {
    "THY": "Türk Hava Yolları",
    "GARAN": "Garanti Bankası",
    "AKBNK": "Akbank",
    "EREGL": "Ereğli Demir Çelik",
    "KCHOL": "Koç Holding",
    "DOLAR": "Amerikan Doları",
    "EURO": "Euro",
    "ALTIN": "Altın",
    "GUMUS": "Gümüş",
    "BIST100": "BIST 100 Endeksi"
}
