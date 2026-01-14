"""
Finansal Chatbot - Action Handlers (v4.5 - FINAL)
=================================================
BERT niyetleri, Zemberek analizleri ve yfinance verilerini
birleştirerek kullanıcıya dinamik cevaplar üretir.
"""

import random
import time
import requests
import templates  # templates.py dosyasındaki şablonları kullanır

from config import (
    CACHE_SURESI, HABER_CACHE_SURESI,
    TICKER_MAP, PARA_BIRIMI, VARLIK_ISIM,
    HABER_ARAMA_MAP, TRADINGVIEW_NEWS_MAP, DEEPL_API_KEY
)

# yfinance import
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Pandas & Numpy import (Teknik analiz için)
try:
    import pandas as pd
    import numpy as np
    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False

# trafilatura import (haber içeriği scraping için)
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

# newspaper3k import (alternatif haber scraping)
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

# Selenium import (JavaScript render için)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class TeknikAnaliz:
    def analiz_et(self, symbol):
        """Hisse için teknik indikatörleri hesaplar: RSI, SMA, Trend"""
        if not YFINANCE_AVAILABLE or not ANALYSIS_AVAILABLE:
            return None
        
        try:
            # Son 6 aylık veriyi çek
            ticker = TICKER_MAP.get(symbol, symbol)
            # Yfinance sembol düzeltme (BIST için .IS ekle)
            if symbol in ["THY", "GARAN", "AKBNK", "EREGL", "KCHOL", "BIST100"]:
                if not ticker.endswith(".IS") and not ticker.startswith("^"):
                    ticker += ".IS"
            
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty or len(df) < 50:
                print(f"   > [ANALİZ] Yetersiz veri: {ticker}")
                return None
            
            # Kapanış fiyatları (MultiIndex kontrolü)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            close = df['Close']
            
            # Son değeri güvenli al
            last_val = close.iloc[-1]
            if hasattr(last_val, 'item'):
                current_price = float(last_val.item())
            else:
                current_price = float(last_val)
            
            # 1. RSI (Göreceli Güç Endeksi) - 14 günlük
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            rsi_val = rsi.iloc[-1]
            if hasattr(rsi_val, 'item'):
                current_rsi = float(rsi_val.item())
            else:
                current_rsi = float(rsi_val)
            
            # 2. Hareketli Ortalamalar (Trend)
            sma50_series = close.rolling(window=50).mean()
            sma50_val = sma50_series.iloc[-1]
            if hasattr(sma50_val, 'item'):
                sma50 = float(sma50_val.item())
            else:
                sma50 = float(sma50_val)
            
            sma200 = None
            if len(df) > 200:
                sma200_series = close.rolling(window=200).mean()
                sma200_val = sma200_series.iloc[-1]
                if hasattr(sma200_val, 'item'):
                    sma200 = float(sma200_val.item())
                else:
                    sma200 = float(sma200_val)
            
            # 3. Yorumlama
            sinyal = "NÖTR"
            trend = "YATAY"
            
            if current_rsi < 30: sinyal = "AŞIRI SATIM (Tepki Gelebilir)"
            elif current_rsi > 70: sinyal = "AŞIRI ALIM (Düzeltme Gelebilir)"
            
            if current_price > sma50: trend = "YÜKSELİŞ (Boğa)"
            else: trend = "DÜŞÜŞ (Ayı)"
            
            return {
                "fiyat": current_price,
                "rsi": round(current_rsi, 2),
                "sma50": round(float(sma50), 2),
                "trend": trend,
                "sinyal": sinyal
            }
        except Exception as e:
            print(f"   > [ANALİZ] Teknik analiz hatası: {e}")
            return None

# =============================================================================
# CACHE SİSTEMİ
# =============================================================================

_fiyat_cache = {}
_haber_cache = {}
_sirket_cache = {}

def _cache_kontrol(cache, anahtar, sure):
    if anahtar in cache:
        veri, zaman = cache[anahtar]
        if time.time() - zaman < sure:
            return veri
    return None

def _cache_kaydet(cache, anahtar, veri):
    cache[anahtar] = (veri, time.time())

# =============================================================================
# ACTION: HABER GETİR (Google RSS + Selenium Scraping + TradingView Fallback)
# =============================================================================

class ActionHaberGetir:
    def execute(self, varlik, soru, **kwargs):
        varlik_isim = VARLIK_ISIM.get(varlik, varlik)
        
        # Cache kontrolü
        cached = _cache_kontrol(_haber_cache, varlik, HABER_CACHE_SURESI)
        if cached:
            return self._formatla(varlik_isim, cached)
        
        # 1. Google News RSS'den haber başlıklarını çek
        haberler = self._google_news_cek(varlik)
        
        # 2. RSS başarısız olursa TradingView'dan çek
        if not haberler or len(haberler) == 0:
            print("   > [HABER] Google RSS başarısız, TradingView'a geçiliyor...")
            haberler = self._tradingview_cek(varlik)
        
        if haberler is None: 
            return random.choice(templates.HABER_HATA)
        if not haberler: 
            return random.choice(templates.HABER_YOK).format(varlik=varlik_isim)
        
        _cache_kaydet(_haber_cache, varlik, haberler)
        return self._formatla(varlik_isim, haberler)
    
    def _tradingview_cek(self, varlik):
        """TradingView News Flow'dan Selenium ile haber çek"""
        if not SELENIUM_AVAILABLE:
            print("   > [HABER] Selenium yok, TradingView atlanıyor")
            return None
        
        url = TRADINGVIEW_NEWS_MAP.get(varlik)
        if not url:
            print(f"   > [HABER] TradingView URL bulunamadı: {varlik}")
            return None
        
        driver = None
        try:
            import time as _time
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            chrome_options.add_argument("--log-level=3")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(20)
            
            print(f"   > [HABER] TradingView: {url[:50]}...")
            driver.get(url)
            _time.sleep(3)  # JavaScript render için bekle
            
            # Haber öğelerini bul
            haberler = []
            news_items = driver.find_elements(By.CSS_SELECTOR, ".news-item, .item-row, article")
            
            for item in news_items[:5]:
                try:
                    # Başlık
                    title_elem = item.find_element(By.CSS_SELECTOR, ".title, h3, .headline, a")
                    title = title_elem.text.strip() if title_elem else ""
                    
                    # Açıklama
                    desc = ""
                    try:
                        desc_elem = item.find_element(By.CSS_SELECTOR, ".description, .summary, p")
                        desc = desc_elem.text.strip()[:400] if desc_elem else ""
                    except:
                        pass
                    
                    # Tarih
                    date = ""
                    try:
                        date_elem = item.find_element(By.CSS_SELECTOR, ".time, .date, time")
                        date = date_elem.text.strip() if date_elem else ""
                    except:
                        pass
                    
                    if title and len(title) > 10:
                        haberler.append({
                            "title": title,
                            "description": desc,
                            "source": "TradingView",
                            "url": "",
                            "date": date
                        })
                except:
                    continue
            
            driver.quit()
            
            if haberler:
                print(f"   > [HABER] TradingView'dan {len(haberler)} haber alındı")
                return haberler
            else:
                print("   > [HABER] TradingView'dan haber bulunamadı")
                return None
                
        except Exception as e:
            if driver:
                driver.quit()
            print(f"   > [HABER] TradingView hatası: {e}")
            return None
    
    def _tarih_formatla(self, tarih_str):
        """Tarih stringini formatla"""
        if not tarih_str:
            return ""
        try:
            from datetime import datetime
            dt = datetime.strptime(tarih_str[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d.%m.%Y %H:%M")
        except:
            return ""
    
    def _icerik_cek(self, url):
        """URL'den haber içeriğini scrape et - Selenium öncelikli"""
        if not url:
            return ""
        
        # Önce Selenium dene (Google News redirect'lerini en iyi takip eder)
        if SELENIUM_AVAILABLE:
            try:
                text = self._selenium_scrape(url)
                if text and len(text) > 50:
                    return text
            except Exception as e:
                print(f"   > [SCRAPE] Selenium hatası: {e}")
        
        # Fallback 1: newspaper3k
        if NEWSPAPER_AVAILABLE:
            try:
                article = Article(url)
                article.download()
                article.parse()
                
                text = article.text
                if text and len(text) > 50:
                    text = text.strip()[:500]
                    if len(text) == 500:
                        text += "..."
                    print(f"   > [SCRAPE] newspaper3k: {len(text)} karakter")
                    return text
            except Exception as e:
                print(f"   > [SCRAPE] newspaper3k hatası: {e}")
        
        # Fallback 2: trafilatura
        if TRAFILATURA_AVAILABLE:
            try:
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
                    if text and len(text) > 50:
                        text = text.strip()[:500]
                        if len(text) == 500:
                            text += "..."
                        print(f"   > [SCRAPE] trafilatura: {len(text)} karakter")
                        return text
            except Exception as e:
                print(f"   > [SCRAPE] trafilatura hatası: {e}")
        
        return ""
    
    def _selenium_scrape(self, url):
        """Selenium ile haber içeriği çek"""
        driver = None
        try:
            import time as _time
            
            # Headless Chrome ayarları
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            chrome_options.add_argument("--log-level=3")
            
            # ChromeDriver başlat
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(20)  # 20 saniye timeout
            
            # Sayfaya git
            driver.get(url)
            
            # Google News ise redirect'i bekle (max 5 saniye)
            if "news.google.com" in url:
                for _ in range(10):  # 10 x 0.5s = 5 saniye
                    _time.sleep(0.5)
                    current = driver.current_url
                    if "news.google.com" not in current and "google.com" not in current:
                        break
            
            # Final URL'yi logla
            final_url = driver.current_url
            print(f"   > [SCRAPE] Selenium: {final_url[:60]}...")
            
            # Hala Google'da ise başarısız
            if "google.com" in final_url:
                driver.quit()
                print("   > [SCRAPE] Redirect başarısız, hala Google'da")
                return ""
            
            # Sayfa içeriğini al - önce paragrafları dene
            content = ""
            
            # Paragraf selector'ları
            p_selectors = [
                "article p", ".article-body p", ".news-detail p", 
                ".content-text p", ".post-content p", "main p", "#content p",
                ".article p", ".news p", ".detail p", "p"
            ]
            
            for selector in p_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        paragraphs = []
                        for elem in elements[:15]:  # Max 15 paragraf
                            text = elem.text.strip()
                            # Kısa satırları filtrele (20 karakter)
                            if len(text) > 20:
                                paragraphs.append(text)
                        
                        if paragraphs:
                            content = ' '.join(paragraphs)
                            if len(content) > 100:  # En az 100 karakter
                                break
                except:
                    continue
            
            # Fallback: article veya main tag'inin tamamını al
            if len(content) < 100:
                for tag in ["article", "main", ".content", "#content"]:
                    try:
                        elem = driver.find_element(By.CSS_SELECTOR, tag)
                        text = elem.text.strip()
                        if len(text) > len(content):
                            content = text
                    except:
                        continue
            
            driver.quit()
            
            if content and len(content) > 50:
                import re
                # Gereksiz boşlukları ve newline'ları temizle
                content = re.sub(r'\n+', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()
                
                # İlk 600 karakteri al
                content = content[:600]
                if len(content) == 600:
                    content += "..."
                print(f"   > [SCRAPE] Selenium: {len(content)} karakter alındı")
                return content
            
            return ""
            
        except Exception as e:
            if driver:
                driver.quit()
            raise e
    
    def _get_real_url(self, google_news_url):
        """Google News redirect URL'sinden gerçek haber URL'sini al"""
        try:
            import base64
            
            # URL'den article ID'yi çıkar
            # Örnek: https://news.google.com/rss/articles/CBMiXxxx...
            if "/articles/" in google_news_url:
                article_id = google_news_url.split("/articles/")[1].split("?")[0]
                
                # Base64 decode dene (padding ekle)
                try:
                    # Farklı padding kombinasyonları dene
                    for padding in ['', '=', '==', '===']:
                        try:
                            decoded = base64.urlsafe_b64decode(article_id + padding)
                            decoded_str = decoded.decode('utf-8', errors='ignore')
                            
                            # URL'yi bul (http ile başlayan kısım)
                            if 'http' in decoded_str:
                                start = decoded_str.find('http')
                                url_part = decoded_str[start:]
                                # İlk geçersiz karaktere kadar al
                                end_chars = ['\x00', '\x01', '\x02', '\x08', '\x10', '\x12', '\x1a', ' ', '\n', '\r']
                                for char in end_chars:
                                    if char in url_part:
                                        url_part = url_part.split(char)[0]
                                if url_part.startswith('http'):
                                    print(f"   > [SCRAPE] Decoded URL: {url_part[:60]}...")
                                    return url_part
                        except:
                            continue
                except:
                    pass
            
            # Decode başarısız olursa None dön
            print("   > [SCRAPE] URL decode başarısız")
            return None
        except Exception as e:
            print(f"   > [SCRAPE] URL decode hatası: {e}")
            return None
    
    def _gnews_cek(self, varlik):
        """GNews API - Varlık bazlı Türkçe haber araması"""
        try:
            from urllib.parse import quote
            
            # API key kontrolü
            if not GNEWS_API_KEY or GNEWS_API_KEY == "your_gnews_api_key":
                print("   > [HABER] GNews API anahtarı ayarlanmamış, Google News'e düşülüyor...")
                return None
            
            # Varlık için finansal bağlamlı arama terimi kullan
            arama = HABER_ARAMA_MAP.get(varlik, VARLIK_ISIM.get(varlik, varlik))
            arama_encoded = quote(arama)
            
            # GNews Search API - Türkçe haberler
            url = f"https://gnews.io/api/v4/search?q={arama_encoded}&lang=tr&country=tr&max=5&apikey={GNEWS_API_KEY}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"   > [HABER] GNews API hata kodu: {response.status_code}")
                return None
            
            data = response.json()
            
            if data.get("totalArticles", 0) == 0:
                print("   > [HABER] GNews'den haber bulunamadı")
                return None
            
            haberler = []
            for article in data.get("articles", [])[:5]:
                haber = {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "url": article.get("url", ""),
                    "publishedAt": article.get("publishedAt", "")
                }
                haberler.append(haber)
            
            print(f"   > [HABER] GNews'den {len(haberler)} haber alındı")
            return haberler
            
        except Exception as e:
            print(f"   > [HABER] GNews API hatası: {e}")
            return None
    
    def _google_news_cek(self, varlik):
        """Fallback: Google News RSS (başlık + açıklama + kaynak + link)"""
        try:
            import xml.etree.ElementTree as ET
            from urllib.parse import quote
            import html
            import re
            
            arama = quote(HABER_ARAMA_MAP.get(varlik, VARLIK_ISIM.get(varlik, varlik)))
            url = f"https://news.google.com/rss/search?q={arama}&hl=tr&gl=TR&ceid=TR:tr"
            response = requests.get(url, timeout=10)
            if response.status_code != 200: return None
            
            root = ET.fromstring(response.content)
            haberler = []
            
            for item in root.findall(".//item")[:5]:
                title_elem = item.find("title")
                desc_elem = item.find("description")
                source_elem = item.find("source")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                
                # Description HTML içerir, temizle
                description = ""
                if desc_elem is not None and desc_elem.text:
                    desc_html = desc_elem.text
                    # HTML taglerini temizle
                    desc_clean = re.sub(r'<[^>]+>', '', desc_html)
                    # HTML entities temizle (&nbsp; vb.)
                    desc_clean = html.unescape(desc_clean)
                    
                    # Başlık ile aynı/benzer mi kontrol et (gereksiz tekrar engelle)
                    # Tüm özel karakterleri kaldır, sadece alfanumerik karşılaştır
                    def normalize(s):
                        return re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]', '', s.lower())
                    
                    desc_normalized = normalize(desc_clean)
                    title_normalized = normalize(title)
                    
                    # İlk 30 karakter aynı mı veya biri diğerini içeriyor mu?
                    is_similar = (
                        desc_normalized[:30] == title_normalized[:30] or
                        title_normalized in desc_normalized or 
                        desc_normalized in title_normalized
                    )
                    
                    if not is_similar:
                        description = desc_clean.strip()
                
                # Kaynak bilgisi
                source = source_elem.text.strip() if source_elem is not None and source_elem.text else ""
                
                # Link bilgisi - RSS'de link bazen farklı formatta olabilir
                link = ""
                if link_elem is not None:
                    if link_elem.text:
                        link = link_elem.text.strip()
                    elif link_elem.tail:
                        link = link_elem.tail.strip()
                
                # Debug: URL ve description durumunu logla
                print(f"   > [DEBUG] Title: {title[:40]}... | URL: {'VAR' if link else 'YOK'} | Desc: {'VAR' if description else 'BOŞ'}")
                
                # Yayın tarihi
                pub_date = ""
                if pub_date_elem is not None and pub_date_elem.text:
                    # "Sat, 11 Jan 2026 10:30:00 GMT" formatını sadeleştir
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(pub_date_elem.text, "%a, %d %b %Y %H:%M:%S %Z")
                        pub_date = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        pub_date = ""
                
                haberler.append({
                    "title": title,
                    "description": description,
                    "source": source,
                    "url": link,
                    "date": pub_date
                })
            
            print(f"   > [HABER] Google News RSS'den {len(haberler)} haber alındı")
            return haberler
        except Exception as e:
            print(f"   > [HABER] Google News RSS hatası: {e}")
            return None
    
    def _formatla(self, varlik_isim, haberler):
        giris = random.choice(templates.HABER_GIRIS).format(varlik=varlik_isim)
        items = []
        
        for idx, h in enumerate(haberler[:5]):  # Max 5 haber dene
            if len(items) >= 3:  # Max 3 göster
                break
                
            title = h.get('title', '')
            source = h.get('source', '')
            date = h.get('date', '')
            url = h.get('url', '')
            desc = h.get('description', '')  # TradingView'dan geliyorsa dolu olacak
            
            # Description yoksa ve URL varsa scrape et
            if (not desc or len(desc) < 30) and url:
                desc = self._icerik_cek(url)
            
            # İçerik yoksa bu haberi atla
            if not desc or len(desc) < 30:
                continue
            
            # Kaynak ve tarih satırı oluştur
            meta_parts = []
            if source:
                meta_parts.append(source)
            if date:
                meta_parts.append(date)
            meta_line = " | ".join(meta_parts) if meta_parts else ""
            
            if meta_line:
                items.append(f"  📰 **{title}**\n     _{meta_line}_\n     {desc}")
            else:
                items.append(f"  📰 **{title}**\n     {desc}")
        
        # Hiç içerik bulunamadıysa
        if not items:
            return random.choice(templates.HABER_YOK).format(varlik=varlik_isim)
        
        kapan = random.choice(templates.HABER_KAPAN)
        return f"{giris}\n\n" + "\n\n".join(items) + f"\n\n{kapan}"

# =============================================================================
# ACTION: ŞİRKET BİLGİSİ
# =============================================================================

class ActionSirketBilgisi:
    def execute(self, varlik, soru, **kwargs):
        varlik_isim = VARLIK_ISIM.get(varlik, varlik)
        cached = _cache_kontrol(_sirket_cache, varlik, CACHE_SURESI * 2)
        if cached: return self._formatla(varlik_isim, cached)
        
        bilgi = self._bilgi_cek(varlik)
        if not bilgi: return random.choice(templates.SIRKET_BILGI_YOK).format(varlik=varlik_isim)
        
        _cache_kaydet(_sirket_cache, varlik, bilgi)
        return self._formatla(varlik_isim, bilgi)
    
    def _ceviri_yap(self, text):
        """DeepL API ile metni Türkçe'ye çevirir"""
        if not text or len(text) < 5 or "DEEPL" not in globals() and not DEEPL_API_KEY:
            return text
            
        try:
            # DeepL API URL (Free veya Pro)
            url = "https://api-free.deepl.com/v2/translate"
            if DEEPL_API_KEY and not DEEPL_API_KEY.endswith(":fx"):
                url = "https://api.deepl.com/v2/translate"
            
            payload = {
                "auth_key": DEEPL_API_KEY,
                "text": text,
                "target_lang": "TR"
            }
            
            response = requests.post(url, data=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if "translations" in result and len(result["translations"]) > 0:
                    return result["translations"][0]["text"]
            else:
                print(f"   > [ÇEVİRİ] DeepL Hatası ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"   > [ÇEVİRİ] İstek hatası: {e}")
            
        return text

    def _bilgi_cek(self, varlik):
        if not YFINANCE_AVAILABLE: return None
        ticker_kod = TICKER_MAP.get(varlik)
        
        # BIST düzeltmesi
        if varlik in ["THY", "GARAN", "AKBNK", "EREGL", "KCHOL", "BIST100"]:
            if not ticker_kod.endswith(".IS") and not ticker_kod.startswith("^"):
                ticker_kod += ".IS"
        
        if not ticker_kod: return None
        
        # Kategori Belirleme
        category = "HISSE"  # Varsayılan
        if "XU100" in ticker_kod or "^" in ticker_kod: category = "ENDEKS"
        elif "=X" in ticker_kod: category = "DOVIZ"
        elif "=F" in ticker_kod or "GC" in ticker_kod or "SI" in ticker_kod: category = "EMTIA"
        
        try:
            ticker = yf.Ticker(ticker_kod)
            info = ticker.info
            
            # --- HİSSE SENEDİ ÖZEL VERİLERİ ---
            if category == "HISSE":
                f_k = info.get("trailingPE", info.get("forwardPE", 0))
                market_cap = info.get("marketCap", 0)
                high_52 = info.get("fiftyTwoWeekHigh", 0)
                low_52 = info.get("fiftyTwoWeekLow", 0)
                
                # Tavsiye Türkçeleştirme
                rec_map = {
                    "Strong Buy": "Güçlü AL 🟢",
                    "Buy": "AL 🟢",
                    "Hold": "TUT 🟡",
                    "Sell": "SAT 🔴",
                    "Strong Sell": "Güçlü SAT 🔴",
                    "Underperform": "Endeks Altı 📉",
                    "Outperform": "Endeks Üzeri 📈"
                }
                rec_key = info.get("recommendationKey", "nötr").replace("_", " ").title()
                recommendation = rec_map.get(rec_key, rec_key)
                
                # Özet ve Çeviri
                summary_raw = info.get("longBusinessSummary", "")
                summary = ""
                if summary_raw:
                    ozet_kisa = summary_raw[:400].rsplit('.', 1)[0] + "."
                    summary = self._ceviri_yap(ozet_kisa)
                
                # Sektör Çevirisi
                sector = self._ceviri_yap(info.get("sector", "Genel"))
                industry = self._ceviri_yap(info.get("industry", ""))
                
                # Piyasa Değeri Formatlama (milyar)
                if market_cap:
                    market_cap = f"{market_cap / 1_000_000_000:.2f} Milyar"
                
                return {
                    "category": category,
                    "sector": sector,
                    "industry": industry,
                    "summary": summary if summary else "Bilgi bulunamadı.",
                    "market_cap": market_cap,
                    "pe_ratio": round(f_k, 2) if f_k else "N/A",
                    "high_52": high_52,
                    "low_52": low_52,
                    "recommendation": recommendation,
                    "currency": info.get("currency", "TRY")
                }
            
            # --- DÖVİZ / EMTİA / ENDEKS VERİLERİ ---
            else:
                return {
                    "category": category,
                    "open": info.get("open", 0),
                    "prev_close": info.get("previousClose", 0),
                    "day_low": info.get("dayLow", 0),
                    "day_high": info.get("dayHigh", 0),
                    "volume": info.get("volume", 0),
                    "currency": info.get("currency", "")
                }
                
        except: return None

    def _formatla(self, varlik_isim, bilgi):
        category = bilgi.get("category", "HISSE")
        
        if category == "HISSE":
            giris = random.choice(templates.KARNE_GIRIS).format(varlik=varlik_isim)
            ozet = f"\n🏢 **Sektör:** {bilgi['sector']} / {bilgi['industry']}\n"
            finansallar = (
                f"💰 **Piyasa Değeri:** {bilgi['market_cap']} {bilgi['currency']}\n"
                f"📉 **F/K Oranı:** {bilgi['pe_ratio']} (Yatırım Geri Dönüş Süresi)\n"
                f"↕️ **52 Haftalık Aralık:** {bilgi['low_52']} - {bilgi['high_52']}\n"
                f"🎯 **Analist Konsensusu:** {bilgi['recommendation']}\n"
            )
            aciklama = f"\nℹ️ **Şirket Hakkında:** {bilgi['summary']}"
            return giris + ozet + finansallar + aciklama
            
        else:
            # Döviz/Emtia/Endeks Gösterimi
            giris = f"📊 **{varlik_isim} Piyasa Verileri** ({category})\n"
            
            # Para birimi düzeltme (USDTRY için "TRY" göstermek saçma olabilir, boşver)
            curr = bilgi['currency']
            
            finansallar = (
                f"\n📉 **Önceki Kapanış:** {bilgi['prev_close']} {curr}\n"
                f"🌅 **Açılış:** {bilgi['open']} {curr}\n"
                f"↕️ **Günlük Aralık:** {bilgi['day_low']} - {bilgi['day_high']}\n"
            )
            
            if bilgi.get('volume'):
                finansallar += f"📊 **Hacim:** {bilgi['volume']:,}\n"
                
            not_bilgisi = "\n_Bu varlık türü için temel bilanço verileri sunulmamaktadır._"
            
            return giris + finansallar + not_bilgisi

# =============================================================================
# ACTION: FİYAT SORGULA
# =============================================================================

class ActionFiyatSorgula:
    def execute(self, varlik, soru, **kwargs):
        varlik_isim = VARLIK_ISIM.get(varlik, varlik)
        para = PARA_BIRIMI.get(varlik, "TL")
        
        fiyat = _cache_kontrol(_fiyat_cache, varlik, CACHE_SURESI)
        if fiyat is None:
            fiyat = self._fiyat_cek(varlik)
            if fiyat: _cache_kaydet(_fiyat_cache, varlik, fiyat)
        
        if fiyat is None: 
            return random.choice(templates.FIYAT_HATA).format(varlik_isim=varlik_isim)
        
        # Türkçe sayı formatı (Örn: 284.50 -> 284,50)
        fiyat_str = f"{fiyat:,.2f} {para}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        return random.choice(templates.FIYAT_BASARILI).format(varlik_isim=varlik_isim, fiyat=fiyat_str)
    
    def _fiyat_cek(self, varlik):
        if not YFINANCE_AVAILABLE: return None
        ticker_kod = TICKER_MAP.get(varlik)
        try:
            # history metodu daha stabildir
            ticker = yf.Ticker(ticker_kod)
            data = ticker.history(period="1d")
            return float(data['Close'].iloc[-1]) if not data.empty else None
        except: return None

# =============================================================================
# ACTION: TREND ANALİZ
# =============================================================================

class ActionTrendAnaliz:
    def execute(self, varlik, soru, **kwargs):
        varlik_isim = VARLIK_ISIM.get(varlik, varlik)
        
        # Teknik Analiz Verisi
        analizci = TeknikAnaliz()
        teknik = analizci.analiz_et(varlik)
        
        # Analist Hedef Fiyatları
        hedef_fiyat = self._hedef_fiyat_cek(varlik)
        
        giris = random.choice(templates.ANALIST_GIRIS).format(varlik=varlik_isim)
        
        trend_yorum = ""
        if teknik:
            trend_renk = "Yükseliş" if "YÜKSELİŞ" in teknik['trend'] else "Düşüş"
            trend_yorum = f"\n• **Teknik Trend:** {teknik['trend']} (SMA50'ye göre)\n"
        
        analist_yorum = ""
        if hedef_fiyat:
            potansiyel = hedef_fiyat['potansiyel']
            potansiyel_renk = "🟩" if potansiyel > 0 else "🟥"
            analist_yorum = (
                f"\n🎯 **Analist Konsensusu:**\n"
                f"   • Konsensus: _{hedef_fiyat['tavsiye']}_\n"
                f"   • Hedef Fiyat: {hedef_fiyat['hedef_fiyat']} {hedef_fiyat['para']}\n"
                f"   • Getiri Potansiyeli: {potansiyel_renk} %{potansiyel}\n"
            )
        else:
            analist_yorum = "\n⚠️ Analist hedef fiyat verisine ulaşılamadı.\n"
            
        return giris + trend_yorum + analist_yorum + "\n_Veriler piyasa gecikmeli olabilir._"

    def _hedef_fiyat_cek(self, varlik):
        if not YFINANCE_AVAILABLE: return None
        ticker_kod = TICKER_MAP.get(varlik)
        
        # BIST düzeltmesi
        if varlik in ["THY", "GARAN", "AKBNK", "EREGL", "KCHOL", "BIST100"]:
            if not ticker_kod.endswith(".IS") and not ticker_kod.startswith("^"):
                ticker_kod += ".IS"
                
        try:
            info = yf.Ticker(ticker_kod).info
            current = info.get("currentPrice") or info.get("previousClose")
            target = info.get("targetMeanPrice")
            
            # Tavsiye Türkçeleştirme
            rec_map = {
                "Strong Buy": "Güçlü AL 🟢",
                "Buy": "AL 🟢",
                "Hold": "TUT 🟡",
                "Sell": "SAT 🔴",
                "Strong Sell": "Güçlü SAT 🔴",
                "Underperform": "Endeks Altı 📉",
                "Outperform": "Endeks Üzeri 📈"
            }
            rec_key = info.get("recommendationKey", "nötr").replace("_", " ").title()
            tavsiye = rec_map.get(rec_key, rec_key)
            
            if current and target:
                potansiyel = ((target - current) / current) * 100
                return {
                    "hedef_fiyat": target,
                    "potansiyel": round(potansiyel, 2),
                    "tavsiye": tavsiye,
                    "para": info.get("currency", "TRY")
                }
            return None
        except: return None

# =============================================================================
# ACTION: ALIM-SATIM (ELIZA & ZEMBEREK ENTEGRASYONU)
# =============================================================================


class ActionAlimSatimUyari:
    def execute(self, varlik, soru, **kwargs):
        """Kullanıcının alım-satım sorusuna teknik analiz ile cevap verir"""
        varlik_isim = VARLIK_ISIM.get(varlik, varlik)
        
        # Teknik Analiz yap
        analizci = TeknikAnaliz()
        veri = analizci.analiz_et(varlik)
        
        giris = random.choice(templates.TEKNIK_GIRIS).format(varlik=varlik_isim)
        
        if veri:
            # RSI Durumu
            rsi_renk = "🟢" if veri['rsi'] < 30 else "🔴" if veri['rsi'] > 70 else "🟡"
            
            # Trend Durumu
            trend_renk = "📈" if "YÜKSELİŞ" in veri['trend'] else "📉"
            
            detay = (
                f"\n• **Güncel Fiyat:** {veri['fiyat']:.2f} {PARA_BIRIMI.get(varlik, '')}\n"
                f"• **Trend:** {trend_renk} {veri['trend']}\n"
                f"• **RSI (14):** {rsi_renk} {veri['rsi']} -> _{veri['sinyal']}_\n"
                f"• **50 Günlük Ort:** {veri['sma50']}\n"
            )
            
            yorum = random.choice(templates.TEKNIK_OZET_GIRIS)
            if veri['rsi'] < 30:
                yorum += "Fiyat teknik olarak 'ucuz' bölgede (aşırı satım). Tepki yükselişi beklenebilir."
            elif veri['rsi'] > 70:
                yorum += "Fiyat teknik olarak 'pahalı' bölgede (aşırı alım). Kar satışı gelebilir."
            elif "YÜKSELİŞ" in veri['trend']:
                yorum += "Orta vadeli yükseliş trendi korunuyor. Trend desteği takip edilmeli."
            else:
                yorum += "Düşüş trendi baskın görünüyor. Temkinli olunmalı."
            
            uyari = "\n\n⚠️ _Bu bir yatırım tavsiyesi değildir. Sadece matematiksel gösterge analizidir._"
            
            return giris + detay + yorum + uyari
        
        else:
            # Veri çekilemezse standart uyarı dön
            return random.choice(templates.ALIM_UYARI).format(varlik=varlik_isim, zaman="şu an")

# =============================================================================
# ACTION MAPPING & EXECUTION
# =============================================================================

ACTION_MAP = {
    'Genel Bilgi/Durum': ActionSirketBilgisi(),
    'Risk ve Haber Analizi': ActionHaberGetir(),
    'Hedef Fiyat Sorgulama': ActionFiyatSorgula(),
    'Alım-Satım Niyeti': ActionAlimSatimUyari(),
    'Piyasa Trend/Tahmin': ActionTrendAnaliz(),
}

def execute_action(niyet, varlik, soru, analiz=None):
    """
    Doğru action sınıfını bulur ve Zemberek analizini iletir.
    """
    action = ACTION_MAP.get(niyet)
    if action:
        # analiz verisi 'analiz' anahtar kelimesiyle gönderilir
        return action.execute(varlik, soru, analiz=analiz)
    return ACTION_MAP['Genel Bilgi/Durum'].execute(varlik, soru)