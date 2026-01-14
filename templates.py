"""
Finansal Chatbot - Doğal Dil Şablonları (v4.5)
==============================================
Bu şablonlar; BERT niyetleri, Zemberek morfolojik analizleri ve 
API hata durumları için chatbot'un sesini oluşturur.
"""

# =============================================================================
# HABER ŞABLONLARI (Risk ve Haber Analizi)
# =============================================================================

HABER_GIRIS = [
    "[HABER] {varlik} hakkında son gelişmelere göz atalım:",
    "[HABER] {varlik} ile ilgili güncel haberleri sizin için derledim:",
    "[HABER] İşte {varlik} piyasasında öne çıkan başlıklar:",
    "[HABER] {varlik} gündeminden önemli notları özetliyorum:",
    "[HABER] {varlik} cephesinde takip etmeniz gereken son haberler:"
]

HABER_ITEM = [
    "  • {baslik}",
    "  > {baslik}",
    "  - {baslik}"
]

HABER_KAPAN = [
    "Daha detaylı bilgi için finansal haber kaynaklarını takip edebilirsiniz.",
    "Haber akışının fiyat üzerindeki etkisini yakından izlemenizi öneririm.",
    "Bu gelişmeleri yatırım stratejilerinizde göz önünde bulundurmalısınız.",
    "Güncel takas verileriyle bu haberleri birleştirmek faydalı olabilir.",
    "Piyasa bu haberleri henüz tam fiyatlamamış olabilir, temkinli olun."
]

HABER_YOK = [
    "{varlik} hakkında şu an öne çıkan güncel bir haber akışı bulunmuyor.",
    "Sistemlerimde {varlik} ile ilgili son 24 saatte kritik bir gelişme tespit edemedim.",
    "{varlik} gündemi şu an oldukça sakin görünüyor."
]

HABER_HATA = [
    "Haber servisinde geçici bir sorun var, gelişmelere şu an erişilemiyor.",
    "Haber akışı çekilirken teknik bir aksaklık yaşandı.",
    "Haber kaynaklarına erişim sağlanamadı, takas verilerini inceleyebilirsiniz."
]

# =============================================================================
# ŞİRKET BİLGİSİ ŞABLONLARI (Genel Bilgi/Durum)
# =============================================================================

SIRKET_GIRIS = [
    "{varlik_isim} hakkında genel bir değerlendirme yapalım:",
    "İşte {varlik_isim} şirketine dair temel veriler:",
    "{varlik_isim} hakkında bildiğim detayları paylaşıyorum:",
    "Sizin için {varlik_isim} profilini çıkardım:"
]

SIRKET_SEKTOR = [
    "{varlik_isim}, {sektor} sektöründe faaliyet gösteren öncü bir kurumdur.",
    "Şirket, Türkiye'nin {sektor} alanındaki en güçlü oyuncularından biridir.",
    "Sektörel olarak {sektor} içerisinde yer alan {varlik_isim}, piyasa hacmiyle dikkat çekiyor."
]

PIYASA_DEGERI = [
    "Şirketin piyasa değeri yaklaşık {deger} seviyesinde.",
    "Güncel piyasa değeri {deger} civarında seyrediyor.",
    "{varlik_isim} yaklaşık {deger} piyasa değerine sahip."
]

CALISAN_SAYISI = [
    "Şirkette yaklaşık {sayi} çalışan bulunuyor.",
    "Personel sayısı yaklaşık {sayi} kişi olarak kaydedilmiş."
]

SIRKET_BILGI_YOK = [
    "{varlik} için detaylı şirket bilgisine şu an ulaşılamıyor.",
    "Şirket profili verisi geçici olarak erişilemez durumda.",
    "{varlik} hakkında detaylı bilgi için resmi kaynakları incelemenizi öneririm."
]

# =============================================================================
# FİYAT ŞABLONLARI (Hedef Fiyat Sorgulama)
# =============================================================================

FIYAT_BASARILI = [
    "[FİYAT] {varlik_isim} anlık işlem fiyatı: {fiyat}",
    "[FİYAT] {varlik_isim} şu an piyasada {fiyat} seviyesinden alıcı buluyor.",
    "[FİYAT] Güncel verilere göre {varlik_isim}: {fiyat}",
    "[FİYAT] {varlik_isim} için son kaydedilen rakam: {fiyat}"
]

FIYAT_HATA = [
    "{varlik_isim} için anlık fiyat bilgisi şu an alınamıyor. Lütfen daha sonra tekrar deneyin.",
    "Fiyat servislerimizde geçici bir yoğunluk var, {varlik_isim} verisine ulaşamadım.",
    "Piyasa verileri şu an güncelleniyor, {varlik_isim} fiyatını birazdan tekrar sorabilirsiniz."
]

# =============================================================================
# TREND ANALİZ ŞABLONLARI (Piyasa Trend/Tahmin)
# =============================================================================

TREND_GIRIS = [
    "[ANALİZ] {varlik_isim} teknik görünümü üzerine notlarım:",
    "[ANALİZ] Grafik verilerine göre {varlik_isim} sinyalleri:",
    "[ANALİZ] {varlik_isim} için kısa vadeli teknik beklentiler:"
]

TREND_YUKSELIS = [
    "[YÜKSELİŞ] Teknik göstergeler {varlik_isim} için pozitif bir ivmeye işaret ediyor.",
    "[YÜKSELİŞ] {varlik_isim} üzerinde alım iştahı artmış görünüyor, RSI seviyesi bunu destekliyor.",
    "[YÜKSELİŞ] {varlik_isim} direnç bölgesini zorluyor, hacimli bir kırılım yükselişi hızlandırabilir."
]

TREND_DUSUS = [
    "[DÜŞÜŞ] {varlik_isim} grafiğinde satış baskısının arttığı gözlemleniyor.",
    "[DÜŞÜŞ] Teknik olarak {varlik_isim} için destek seviyelerinin test edilmesi muhtemel.",
    "[DÜŞÜŞ] Kısa vadeli göstergeler {varlik_isim} tarafında temkinli olunması gerektiğini söylüyor."
]

TREND_NOTR = [
    "[NÖTR] {varlik_isim} şu an yatay bir bantta hareket ediyor.",
    "[NÖTR] Teknik göstergeler {varlik_isim} için şu an net bir yön sinyali üretmiyor.",
    "[NÖTR] Karar aşamasında olan {varlik_isim} için hacim verilerini takip etmek mantıklı olabilir."
]

TREND_KAPAN = [
    "Bu analiz teknik veriler ışığında hazırlanmıştır.",
    "Göstergelerin yanı sıra temel analiz verilerini de incelemeniz faydalı olur."
]

TREND_HATA = [
    "{varlik_isim} için teknik analiz verisi şu an alınamıyor.",
    "Grafik verileri yetersiz olduğu için trend analizi yapılamadı.",
    "İndikatörler hesaplanırken bir hata oluştu, lütfen tekrar deneyin."
]

# =============================================================================

# =============================================================================
# TEKNIK ANALIZ & KARNE ŞABLONLARI
# =============================================================================

KARNE_GIRIS = [
    "📊 **{varlik} Finansal Karnesi**\n",
    "🏢 İşte **{varlik}** için temel analiz özetim:\n",
    "🔍 **{varlik}** finansal sağlığına yakından bakalım:\n",
    "📋 Sizin için **{varlik}** şirket profilini inceledim:\n",
    "💼 **{varlik}** temel verileri şu şekilde:\n"
]

TEKNIK_GIRIS = [
    "🔍 **{varlik} Teknik Analiz Raporu**\n",
    "📈 **{varlik}** grafiklerini sizin için taradım:\n",
    "⚙️ İşte **{varlik}** için matematiksel göstergelerin durumu:\n",
    "🔢 **{varlik}** teknik indikatör özeti:\n",
    "📉 **{varlik}** fiyat hareketleri ve sinyaller:\n"
]

TEKNIK_OZET_GIRIS = [
    "\n💡 **Özet Değerlendirme:** ",
    "\n📌 **Teknik Görünüm:** ",
    "\n🤖 **Yapay Zeka Yorumu:** ",
    "\n📝 **Sonuç Olarak:** ",
    "\n🧠 **Analiz Notu:** "
]

ANALIST_GIRIS = [
    "📈 **{varlik} Piyasa Trend ve Beklenti Analizi**\n",
    "🎯 **{varlik}** için piyasa profesyonelleri ne düşünüyor?\n",
    "🔮 **{varlik}** gelecek projeksiyonu ve analist hedefleri:\n",
    "🔭 **{varlik}** yatırımcıları için orta vadeli beklentiler:\n"
]

# ALIM-SATIM & ELIZA YANSITMA (İşlem ve Portföy Niyeti)
# =============================================================================

YANSITMA_SABLONLARI = [
    "Anlıyorum, {varlik} üzerinde bir {fiil} işlemi yapmayı {zaman} içerisinde mi planlıyorsunuz?",
    "Bahsettiğiniz {fiil} eylemi için {varlik} grafiklerindeki son durumu incelediniz mi?",
    "Portföyünüzde {varlik} için {fiil} kararını verirken hangi riskleri göz önüne aldınız?",
    "Şu anki piyasa konjonktüründe {varlik} için {fiil} düşüncesi oldukça stratejik görünüyor."
]

ALIM_UYARI = [
    "[UYARI] {varlik} için alım kararı vermeden önce risk toleransınızı mutlaka gözden geçirin.",
    "[UYARI] {varlik} almayı düşünüyorsanız, kademeli alım stratejisi maliyet avantajı sağlayabilir.",
    "[UYARI] Alım yönündeki niyetiniz {zaman} odaklıysa, temel analiz verileri daha kritik hale gelir."
]

SATIM_UYARI = [
    "[UYARI] {varlik} satış kararı için mevcut kar/zarar hedeflerinize sadık kalmanızı öneririm.",
    "[UYARI] {varlik} tarafında bir çıkış planlıyorsanız, işlem hacmini takip etmekte fayda var.",
    "[UYARI] Satış niyetinizin arkasında bir haber akışı mı var yoksa teknik bir düzeltme mi bekliyorsunuz?"
]

GENEL_ALIM_SATIM = [
    "[UYARI] {varlik_isim} alım-satım kararları kişisel risk toleransınıza bağlıdır.",
    "{varlik_isim} için işlem yapmadan önce piyasa koşullarını değerlendirmenizi öneririm.",
    "⚠️ Yatırım tavsiyesi değildir. {varlik_isim} kararlarınızı kendi analizinize dayandırın."
]

# =============================================================================
# YASAL UYARI VE SABİTLER
# =============================================================================

YTD_NOTU = "\n\n⚠️ Not: Paylaşılan bilgiler kişisel analizler olup yatırım tavsiyesi niteliği taşımaz."