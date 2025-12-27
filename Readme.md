# 🚀 Janebi Dashboard
<p align="center">
  <strong>Internal Utility Dashboard (Built for Self-Preservation)</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/streamlit-1.51.0-FF4B4B?logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/status-internal-success" />
  <img src="https://img.shields.io/badge/ui-RTL%20Persian-blueviolet" />
</p>

---

## ❓ What is this?

This is a Streamlit dashboard containing tools for tasks that were:
- “simple”
- “quick”
- “can you just do it once?”

They are now buttons.

---

## 🇮🇷 توضیح فارسی (خیلی خلاصه)

این داشبورد ساخته شد چون:
- تولید QR بدون محدودیت
- ادغام اکسل بدون خطا
- یکسان‌سازی شماره‌ها
- حذف داده‌ی تکراری
- اسکریپ عکس محصول
- تبدیل همه عکس‌ها به 512×512  

از من زمان میگرفت.
با این تولکیت دیگه میتونم روی کارای خودم تمرکز کنم.

## 🧰 Tools

### 🏠 Home
Navigation. Nothing surprising.

---

### 🖼️ Product Image Scraper
**`pages/اسکریپر عکس محصول.py`**

- Input:
  - Single URL
  - Excel / CSV
  - Google Sheet (CSV export)
- Action:
  - Scrape main product image
  - Resize
  - Pad
- Output:
  - 512×512 images
  - ZIP
  - errors.txt (for reality)

---

### 🎫 Discount Code Analyzer
**`pages/تحلیل کد تخفیف.py`**

- Upload:
  - Orders file
  - Discount code list
- Result:
  - Matched
  - Unmatched
  - Summary
- Math:
  - Gross
  - Discount
  - Net
- Export:
  - Excel
  - Clean

---

### 🔗 QR Code Generator
**`pages/ساخت کد QR.py`**

- Input:
  - Single link
  - File
  - Google Sheet
- Options:
  - Colors
- Output:
  - PNG
  - ZIP

---

## ⚙️ Requirements

```txt
beautifulsoup4==4.14.3
pandas==2.3.3
Pillow==12.0.0
qrcode==8.2
Requests==2.32.5
streamlit==1.51.0
openpyxl
xlsxwriter
```
---
## ▶️ Run (Recommended: Docker)

```bash
# build image
docker build -t janebi-dashboard .

# run container
docker run -p 8501:8501 janebi-dashboard
```
open
```http://localhost:8501```
No virtualenv. No dependency issues.

## ▶️ Run (Local, if you insist)
```
pip install -r requirements.txt
streamlit run خانه.py
```