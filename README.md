# Qurilish daftari — o'z serveringizda ishlaydigan versiya

Bu — noutbukingizda Python bilan ishga tushiriladigan, keyin bepul serverga
chiqarib, telefondan istalgan joydan ochib bo'ladigan to'liq loyiha.

## 1. Noutbukda ishga tushirish

Terminalni (Windows'da "cmd" yoki "PowerShell", Mac'da "Terminal") oching va:

```bash
cd qurilish-app
pip install -r requirements.txt
uvicorn main:app --reload
```

Keyin brauzerda oching: **http://127.0.0.1:8000**

Shu yerda 4 ta login bilan sinab ko'rishingiz mumkin (kodlarni `main.py`
faylining boshida, `USERS` degan joyda o'zgartirsangiz bo'ladi):

| Ism | Kod | Huquq |
|---|---|---|
| Temur | 7421 | admin — hammani ko'radi |
| Suhrob | 3184 | faqat o'zinikini |
| Kamoladdin | 5902 | faqat o'zinikini |
| Siroj | 6637 | faqat o'zinikini |

Ma'lumotlar `app.db` faylida saqlanadi (avtomatik yaratiladi) — dasturni
yopib-ochsangiz ham yo'qolmaydi.

## 2. Bepul serverga chiqarish (Render.com)

Bu bosqichda dastur internetda doimiy ishlaydigan bo'ladi, sheriklaringiz
telefonidan istalgan joydan kira oladi — noutbukingiz yoqilgan bo'lishi
shart emas.

1. **GitHub'da hisob oching** (agar yo'q bo'lsa) — github.com
2. Shu `qurilish-app` papkasini GitHub'ga yuklang (repository sifatida)
3. **render.com**'da bepul hisob oching (kredit karta talab qilinmaydi)
4. "New +" → "Web Service" → GitHub repository'ingizni tanlang
5. Sozlamalar:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. "Create Web Service" bosing — bir necha daqiqada tayyor bo'ladi
7. Sizga `https://sizning-nomingiz.onrender.com` kabi doimiy havola beriladi

**Muhim eslatma:** Render'ning bepul tarifida, 15 daqiqa hech kim
kirmasa, server "uxlab qoladi" — keyingi safar ochganda 30-50 soniya
kutish kerak bo'lishi mumkin. Bu odatiy holat, xato emas.

## 3. Keyingi qadam — APK

Server tayyor bo'lgach, shu veb-sahifani APK'ga o'rash mumkin bo'ladi
(masalan **Median.co** yoki **PWA Builder** orqali — bular veb-sahifani
"o'rab", Play Market'ga chiqarish mumkin bo'lgan APK qilib beradi).
Bu — server ishga tushib, barqaror ishlayotganini tekshirgandan keyin
qilinadigan alohida bosqich.

## Xavfsizlik haqida eslatma

Bu loyihada parollar oddiy shaklda (`main.py` ichida) saqlangan — bu shaxsiy,
kichik jamoa uchun yetarli, lekin professional darajadagi xavfsizlik emas.
Serverni internetga chiqarganingizdan so'ng, `main.py` faylidagi kodlarni
murakkabroq (masalan 6 xonali, tasodifiy) qilib almashtirishni maslahat
beraman.
