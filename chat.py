import torch
import random
import re
from transformers import BertTokenizer, BertForSequenceClassification
from zemberek import TurkishMorphology, TurkishSentenceNormalizer

# 1. Model ve Çevre Yüklemeleri
model_path = "./finans_model"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path)
model.eval()

morphology = TurkishMorphology.create_with_defaults()
normalizer = TurkishSentenceNormalizer(morphology)

# --- NER KATMANI: VARLIK SÖZLÜĞÜ ---
# Kullanıcı ne derse desin, hangi etikete gitmesi gerektiğini tanımlıyoruz.
ner_sozlugu = {
    "akbank": "AKBNK", "akbnk": "AKBNK", "ak": "AKBNK",
    "thy": "THY", "türk hava yolları": "THY", "turk hava yolları": "THY", "havayolu": "THY",
    "garan": "GARAN", "garanti": "GARAN",
    "eregl": "EREGL", "ereğli": "EREGL", "demir": "EREGL", "erdm": "EREGL",
    "usdtry": "USDTRY", "dolar": "USDTRY", "kur": "USDTRY",
    "altın": "ALTIN", "ons": "ALTIN", "gram": "ALTIN", "gold": "ALTIN",
    "gümüş": "GUMUS", "gumus": "GUMUS", "silver": "GUMUS",
    "bist100": "BIST100", "bist": "BIST100", "endeks": "BIST100", "borsa": "BIST100"
}

label_names = ['Genel Bilgi/Durum', 'Risk ve Haber Analizi', 'Hedef Fiyat Sorgulama', 'Alım-Satım Niyeti', 'Piyasa Trend/Tahmin']

# --- CEVAP HAVUZU ---
cevap_havuzu = {
    'Genel Bilgi/Durum': ["{hisse} hakkında piyasa şu an stabil seyrediyor.", "{hisse} forumlarında gürültü seviyesi yüksek."],
    'Risk ve Haber Analizi': ["{hisse} için jeopolitik riskler (Fed, yaptırım vb.) ön planda.", "{hisse} haber akışı proaktif takip edilmeli."],
    'Hedef Fiyat Sorgulama': ["{hisse} teknik analizlerinde {fiyat} civarı kritik bir eşik.", "{hisse} için analistler {fiyat} bandını tartışıyor."],
    'Alım-Satım Niyeti': ["{hisse} için kademeli alım niyetleri yoğunlaşmış durumda.", "{hisse} portföy dağılımında risk iştahına göre değerlendiriliyor."],
    'Piyasa Trend/Tahmin': ["{hisse} grafiğinde orta vadeli yükseliş kanalı izleniyor.", "{hisse} trend yönü henüz teyit bekliyor olabilir."]
}

# --- NER KATMANI: OTOMATİK VARLIK TESPİTİ ---
def varlik_tespit_et(soru):
    soru_temiz = soru.lower().strip()
    # Cümle içinde sözlükteki anahtarları ara
    for anahtar, ticker in ner_sozlugu.items():
        if anahtar in soru_temiz:
            return ticker
    return None # Hiçbir varlık bulunamadı

def sorgu_hazirla(hisse_etiketi, soru):
    norm = normalizer.normalize(soru)
    analiz = morphology.analyze_sentence(norm)
    results = morphology.disambiguate(norm, analiz).best_analysis()
    kokler = " ".join([res.item.lemma for res in results])
    # Otomatik NER sonucu gelen ticker'ı prefix olarak kullan
    return f"[{hisse_etiketi}] {kokler}"

def niyet_tahmin_et(hisse_etiketi, soru):
    text = sorgu_hazirla(hisse_etiketi, soru)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        pred_idx = torch.argmax(probs).item()
        conf = probs[0][pred_idx].item()
    return label_names[pred_idx], conf

def asistan_cevap_ver(soru):
    # 1. NER Katmanını Çalıştır
    ticker = varlik_tespit_et(soru)
    
    # 2. Belirsizlik Yönetimi
    if ticker is None:
        return "Sorgunuzda analiz edebileceğim bir finansal varlık (Hisse, Altın, Dolar vb.) bulamadım."

    niyet, skor = niyet_tahmin_et(ticker, soru)
    
    if skor < 0.35: # [cite: 58, 255]
        return f"{ticker} ile ilgili sorunuzun niyetinden emin olamadım. Daha teknik sorar mısınız?"

    # 3. Dinamik Cevap
    fiyat_match = re.search(r'\d+', soru)
    fiyat_bilgisi = fiyat_match.group(0) if fiyat_match else "mevcut seviyeler"
    
    final_text = random.choice(cevap_havuzu[niyet]).format(hisse=ticker, fiyat=fiyat_bilgisi)
    return f"[*] Tespit Edilen Varlık: {ticker}\n[*] Niyet: {niyet} (%{skor*100:.1f})\n[>] ASİSTAN: {final_text}"

# --- CANLI DÖNGÜ ---
print("\n" + "="*50)
print(" NER KATMANLI AKILLI ASİSTAN")
print("="*50)

while True:
    user_input = input("\nSiz: ")
    if user_input.lower() == 'exit': break
    print("-" * 30)
    print(asistan_cevap_ver(user_input))