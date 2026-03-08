import streamlit as st
import json
import random
import os
from datetime import datetime
import pytz

# ===================== AYARLAR =====================
TIMEZONE = pytz.timezone("Europe/Istanbul")
GUNLUK_SORU_SAYISI = 10 

st.set_page_config(page_title="Günün Seçilmiş Soruları", page_icon="🌸")
st.title("🌸 Her 2 Dünyamı Güzelleştiren Kadına 🌸")

QUESTIONS_FILE = "questions.json"
MESSAGES_FILE = "messages.json"
PROGRESS_FILE = "progress.json"
WRONG_FILE = "wrong_questions.json"

# ===================== JSON YARDIMCILAR =====================
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== VERİ YÜKLEME =====================
questions = load_json(QUESTIONS_FILE, [])
questions = sorted(questions, key=lambda x: x.get("id", 0))

messages = load_json(MESSAGES_FILE, [])
# Progress'e message_index (mesaj sırası) ekledik
progress = load_json(PROGRESS_FILE, {
    "global_index": 0, 
    "message_index": 0, 
    "last_period": "", 
    "period_counter": 0
})
wrong_ids = load_json(WRONG_FILE, [])

# ===================== ZAMAN KONTROLÜ =====================
now_dt = datetime.now(TIMEZONE)
current_hour = now_dt.hour
today_str = now_dt.strftime("%Y-%m-%d")

# BURADAN SAATLERİ DEĞİŞTİREBİLİRSİN:
# 08:00 ile 20:00 arası "sabah", geri kalan zamanlar "aksam"
# Hassas saat ayarı örneği (08:30 ve 18:30 için)
simdi_toplam_dakika = current_hour * 60 + now_dt.minute

sabah_baslangic = 8 * 60 + 30  # 08:30
aksam_baslangic = 20 * 60 + 30 # 20:30

if sabah_baslangic <= simdi_toplam_dakika < aksam_baslangic:
    current_slot = "sabah"
else:
    current_slot = "aksam"

period_id = f"{today_str}_{current_slot}"

# VAKİT DEĞİŞTİĞİNDE SAYAÇ SIFIRLAMA
if progress["last_period"] != period_id:
    progress["last_period"] = period_id
    progress["period_counter"] = 0 
    save_json(PROGRESS_FILE, progress)

# ===================== YANLIŞ SORULAR (SIDEBAR) =====================
with st.sidebar:
    st.header("📊 İstatistikler")
    st.write(f"✅ Toplam Çözülen: {progress['global_index']}")
    st.write(f"❌ Yanlış Sayısı: {len(wrong_ids)}")
    
    st.divider()
    if st.checkbox("📚 Yanlışlarımı Göster (Kalıcı Listem)"):
        if not wrong_ids:
            st.info("Hiç yanlışın yok, harikasın! 🌸")
        else:
            for q_id in wrong_ids:
                q_item = next((item for item in questions if item["id"] == q_id), None)
                if q_item:
                    with st.expander(f"Soru ID: {q_id}"):
                        st.write(f"**Soru:** {q_item['soru']}")
                        st.write(f"**Doğru:** {q_item['dogru']}")

# ===================== SORU MANTIĞI =====================

if progress["global_index"] >= len(questions):
    st.success("🎉 İnanılmaz! Tüm sorular bitti. Sen bir şampiyonsun! 💖")
    st.balloons()

elif progress["period_counter"] >= GUNLUK_SORU_SAYISI:
    st.warning(f"🌸 Bu vaktin ({current_slot}) için ayrılan {GUNLUK_SORU_SAYISI} soruyu bitirdin.")
    st.info("Bir sonraki vakit diliminde yeni soruların açılacak. Beklemede kal aşkım! ✨")

else:
    current_idx = progress["global_index"]
    q = questions[current_idx]
    
    st.write(f"**Soru {progress['period_counter'] + 1} / {GUNLUK_SORU_SAYISI}**")
    st.subheader(q["soru"])
    
    choice = st.radio("Cevabını seç:", q["secenekler"], key=f"q_{current_idx}")
    
    if st.button("Cevabı Onayla ✅"):
        if choice == q["dogru"]:
            st.balloons()
            
            # --- SIRALI MESAJ MANTIĞI ---
            msg_idx = progress.get("message_index", 0)
            
            # Eğer mesajlar listesi bittiyse başa dön (veya istersen sabit bir mesaj ver)
            if msg_idx >= len(messages):
                msg_idx = 0 # Mesajlar bittiyse 1. mesaja döner
            
            current_msg = messages[msg_idx]
            
            # İLERLEME KAYDI
            progress["global_index"] += 1    
            progress["period_counter"] += 1 
            progress["message_index"] = msg_idx + 1 # Mesaj sırasını bir sonraki için artır
            
            save_json(PROGRESS_FILE, progress)
            
            st.success(f"DOĞRU! 🌟 \n\n 💌 Mesajın: {current_msg}")
            
            if st.button("Sonraki Soruya Geç ➡️"):
                st.rerun()
        else:
            st.error("❌ Yanlış cevap, tekrar dene bakalım 💖")
            
            # Yanlışı dosyaya kalıcı olarak ekle
            if q["id"] not in wrong_ids:
                wrong_ids.append(q["id"])
                save_json(WRONG_FILE, wrong_ids)
