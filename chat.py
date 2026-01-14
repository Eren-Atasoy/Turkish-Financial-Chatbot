"""
Finansal Chatbot - Gelişmiş Inference Script (v4.5)
===================================================
Loglama Özellikli: NER, BERT, Zemberek ve Hafıza süreçlerini izler.
"""

import torch
import random
import re
import templates
from transformers import BertTokenizer, BertForSequenceClassification
from actions import execute_action
from config import GUVEN_ESIK

# =============================================================================
# SİSTEM YÜKLEME VE YAPILANDIRMA
# =============================================================================
print("\n[*] Sistemler başlatılıyor...")

try:
    from zemberek import TurkishMorphology, TurkishSentenceNormalizer
    morphology = TurkishMorphology.create_with_defaults()
    normalizer = TurkishSentenceNormalizer(morphology)
    ZEMBEREK_AVAILABLE = True
    print("[+] [NLP] Zemberek ve Morfoloji motoru yüklendi.")
except Exception as e:
    ZEMBEREK_AVAILABLE = False
    print(f"[!] [NLP] Zemberek yüklenemedi: {e}")

model_path = "./finans_model"
try:
    tokenizer = BertTokenizer.from_pretrained(model_path)
    model = BertForSequenceClassification.from_pretrained(model_path)
    model.eval()
    print("[+] [BERT] Model ve Tokenizer hazır.")
except Exception as e:
    print(f"[!] [BERT] Model yükleme hatası: {e}")

label_names = [
    'Genel Bilgi/Durum', 'Risk ve Haber Analizi', 
    'Hedef Fiyat Sorgulama', 'Alım-Satım Niyeti', 'Piyasa Trend/Tahmin'
]

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
# ANALİZ VE LOGLAMA FONKSİYONLARI
# =============================================================================

def girdi_irdeles(soru):
    """
    Zemberek morfolojisi ile kural tabanlı soru kontrolünü birleştirir (Hibrit Yaklaşım).
    """
    if not ZEMBEREK_AVAILABLE:
        return {"fiil": "işlem", "zaman": "güncel", "soru_mu": "?" in soru}

    # Zemberek Analizi
    analiz = morphology.analyze_and_disambiguate(soru).best_analysis()
    
    # Soru Kelimeleri ve Noktalama Kontrolü (Kural Tabanlı Katman)
    soru_kelimeleri = ["ne", "nasıl", "kaç", "ne kadar", "ne zaman", "niçin", "neden", "kim"]
    soru_temiz = soru.lower().strip()
    
    ozet = {
        "fiil": "belirsiz",
        "zaman": "belirtilmemiş",
        "soru_mu": False
    }

    # 1. Kural: Soru işareti var mı veya soru kelimesi içeriyor mu?
    if soru_temiz.endswith("?") or any(re.search(rf"\b{k}\b", soru_temiz) for k in soru_kelimeleri):
        ozet["soru_mu"] = True

    # 2. Kural: Zemberek etiketlerini kontrol et (mı/mi ekleri için)
    for res in analiz:
        pos = res.item.primary_pos.name
        tags = res.format_string()
        
        # Zemberek 'Quest' etiketini yakalarsa (örn: alacak mısın?)
        if "Quest" in tags or "Question" in tags:
            ozet["soru_mu"] = True
            
        if pos == "Verb":
            ozet["fiil"] = res.item.lemma
            if "Fut" in tags: ozet["zaman"] = "gelecek"
            elif "Past" in tags: ozet["zaman"] = "geçmiş"
            elif "Prog" in tags: ozet["zaman"] = "şimdiki"
            elif "Necess" in tags: ozet["zaman"] = "gereklilik"
            
    print(f"   > [ZEMBEREK] Fiil: '{ozet['fiil']}' | Zaman: '{ozet['zaman']}' | Soru: {ozet['soru_mu']}")
    return ozet
def varlik_bul(text):
    """NER katmanı: Varlık tespiti yapar ve loglar."""
    text_lower = text.lower()
    for anahtar, varlik in ner_sozlugu.items():
        if anahtar in text_lower:
            print(f"   > [NER] Tespit Edilen: {varlik} ('{anahtar}')")
            return varlik
    return None

def tahmin_yap(text):
    """BERT niyet tahmini yapar ve güven skorunu loglar."""
    if ZEMBEREK_AVAILABLE:
        try: text = normalizer.normalize(text)
        except: pass
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        pred_idx = torch.argmax(probs).item()
        guven = probs[0][pred_idx].item()
    
    niyet = label_names[pred_idx]
    print(f"   > [BERT] Tahmin: '{niyet}' | Güven: %{guven*100:.2f}")
    return niyet, guven

# =============================================================================
# DİYALOG HAFIZASI
# =============================================================================

class KonusmaHafizasi:
    def __init__(self):
        self.son_varlik = None
        self.son_niyet = None
        self.gecmis = []
    
    def guncelle(self, varlik, niyet, soru, cevap):
        if varlik: self.son_varlik = varlik
        if niyet: self.son_niyet = niyet
        self.gecmis.append((soru, cevap))
        if len(self.gecmis) > 5: self.gecmis.pop(0)

    def referans_var_mi(self, soru):
        referans_kelimeler = ["peki", "ya", "onun", "bu", "o da", "aynısı", "ne kadar", "ne olur"]
        return any(kelime in soru.lower() for kelime in referans_kelimeler)

hafiza = KonusmaHafizasi()

# =============================================================================
# ANA CEVAP MOTORU
# =============================================================================

def cevap_uret(soru):
    print(f"\n[*] Analiz Başlatıldı: '{soru}'")
    
    # 1. NER Aşaması
    varlik = varlik_bul(soru)
    
    # 2. Hafıza Kontrolü
    if varlik is None:
        if hafiza.referans_var_mi(soru) and hafiza.son_varlik:
            varlik = hafiza.son_varlik
            print(f"   > [MEMORY] Varlık hafızadan çekildi: {varlik}")
        else:
            print("   > [NER] Herhangi bir varlık bulunamadı.")
            return "Hangi hisse veya varlık hakkında konuşuyoruz? (Örn: THY, Altın)"

    # 3. BERT Aşaması
    niyet, guven = tahmin_yap(soru)
    
    # --- CONTEXT OVERRIDE (BAĞLAM DÜZELTME) ---
    # Eğer sadece varlık ismi verilmişse ve bir önceki niyet teknik analiz gibiyse, niyeti koru.
    # Örn: Önce "THY teknik analiz", sonra "peki akbank?" -> Akbank Teknik Analiz
    if varlik and len(soru.split()) <= 3 and niyet == "Genel Bilgi/Durum":
        if hafiza.son_niyet and hafiza.son_niyet != "Genel Bilgi/Durum":
            print(f"   > [MEMORY] Bağlam tespit edildi: '{hafiza.son_niyet}' niyeti korunuyor.")
            niyet = hafiza.son_niyet
    # ----------------------------------------
    
    # Güven kontrolü
    if guven < GUVEN_ESIK:
        print(f"   > [WARN] Güven skoru eşik değerin ({GUVEN_ESIK}) altında!")
        return f"[{varlik}] Bu soruyu tam anlayamadım, finansal bir analiz mi istiyorsunuz?"

    # 4. Zemberek Aşaması
    analiz = girdi_irdeles(soru)

    # 5. Aksiyon Aşaması
    print(f"   > [ACTION] '{niyet}' aksiyonu tetikleniyor...")
    cevap = execute_action(niyet, varlik, soru, analiz=analiz)

    # 6. Sonuç
    sonuc = f"{cevap}\n{templates.YTD_NOTU}"
    hafiza.guncelle(varlik, niyet, soru, sonuc)
    
    print("[*] Analiz Tamamlandı.\n")
    return sonuc

# =============================================================================
# ANA DÖNGÜ
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*55)
    print("      AVA v4.5 - FINANSAL ASISTAN (DEBUG MODE ON)")
    print("="*55)
    print("Çıkış: 'exit' | Logları terminalden izleyebilirsiniz.\n")
    
    while True:
        try:
            user_input = input("Siz: ").strip()
            if user_input.lower() == 'exit': break
            if not user_input: continue
            
            # Cevap üret ve terminale bas
            print(cevap_uret(user_input))
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n[!] Kritik Hata: {e}")