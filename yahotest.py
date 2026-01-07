import yfinance as yf

thy = yf.Ticker("THYAO.IS")
guncel_fiyat = thy.fast_info['last_price']

print(f"THY Güncel/Son Fiyat: {guncel_fiyat:.2f} TL")