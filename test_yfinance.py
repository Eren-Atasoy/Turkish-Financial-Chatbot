"""
yfinance Test Script
====================
Yahoo Finance API'nin çalışıp çalışmadigini test eder.
"""

import yfinance as yf
import sys

# Encoding fix for Windows
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 50)
print("  YFINANCE TEST")
print("=" * 50)

# Test edilecek tickerlar
test_tickerlar = [
    ("Apple (kontrol)", "AAPL"),           # US stock - calismali
    ("THY", "THYAO.IS"),                   # Turk hissesi
    ("USD/TRY", "USDTRY=X"),               # Doviz
]

for isim, ticker in test_tickerlar:
    print(f"\n[*] Test ediliyor: {isim} ({ticker})")
    print("-" * 40)
    
    try:
        t = yf.Ticker(ticker)
        
        # Method 1: history()
        print("  Method 1 - history(period=5d):")
        hist = t.history(period="5d")
        if not hist.empty:
            son_fiyat = hist['Close'].iloc[-1]
            print(f"    [OK] Basarili! Son fiyat: {son_fiyat:.2f}")
        else:
            print("    [X] Veri bos!")
        
        # Method 2: fast_info
        print("  Method 2 - fast_info:")
        try:
            fast = t.fast_info
            if hasattr(fast, 'last_price') and fast.last_price:
                print(f"    [OK] Basarili! Last price: {fast.last_price:.2f}")
            else:
                print("    [X] fast_info bos!")
        except Exception as e:
            print(f"    [X] Hata: {type(e).__name__}")
            
    except Exception as e:
        print(f"  [X] Hata: {type(e).__name__}: {e}")

print("\n" + "=" * 50)
print("Test tamamlandi!")
