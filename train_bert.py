import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# 1. Veriyi Yükle
df = pd.read_csv('training_data_cleaned.csv')

# 2. Etiketleri Sayısal Değerlere Dönüştür
label_map = {
    'Genel Bilgi/Durum': 0,
    'Risk ve Haber Analizi': 1,
    'Hedef Fiyat Sorgulama': 2,
    'Alım-Satım Niyeti': 3,
    'Piyasa Trend/Tahmin': 4
}
df['label'] = df['label'].map(label_map)

# 3. Eğitim ve Test Setine Ayır (%80 Eğitim, %20 Test)
train_texts, test_texts, train_labels, test_labels = train_test_split(
    df['text'].values, df['label'].values, test_size=0.2, random_state=42
)

# 4. Tokenizer'ı Yükle (BERTurk cased modeli)
model_name = "dbmdz/bert-base-turkish-128k-cased"
tokenizer = BertTokenizer.from_pretrained(model_name)

# 5. Dataset Sınıfını Tanımla
class FinancialIntentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):
        text = str(self.texts[item])
        label = self.labels[item]
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

train_dataset = FinancialIntentDataset(train_texts, train_labels, tokenizer)
test_dataset = FinancialIntentDataset(test_texts, test_labels, tokenizer)

# 6. Modeli Yükle (5 sınıf için)
model = BertForSequenceClassification.from_pretrained(model_name, num_labels=5)

# 7. Metrikleri Tanımla
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='weighted')
    acc = accuracy_score(labels, preds)
    return {'accuracy': acc, 'f1': f1, 'precision': precision, 'recall': recall}

# 8. Eğitim Parametreleri
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=5,              # 5 tur eğitim
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=100,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    eval_strategy="epoch",      # Her tur sonunda başarıyı ölç
    save_strategy="epoch",
    load_best_model_at_end=True       # En iyi modeli sakla
)

# 9. Eğitimi Başlat
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics
)

print("[*] Model eğitimi başlıyor...")
trainer.train()

# 10. Modeli Kaydet
model.save_pretrained("./finans_model")
tokenizer.save_pretrained("./finans_model")
print("[BAŞARILI] Model eğitildi ve './finans_model' klasörüne kaydedildi.")