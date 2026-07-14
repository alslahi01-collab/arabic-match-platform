# منصة مطابقة القوائم العربية 🔍

أداة ويب مفتوحة المصدر (Python + Streamlit) لتنظيف وتطبيع ومطابقة أعمدة عربية بين ملفين Excel، مع تطبيق قواعد العربية الـ18 لإصلاح أخطاء الإدخال الشائعة (تاء مربوطة/هاء، ألف بأشكالها، مسافات بعد "عبد"، تشكيل، تطويل…).

---

## ✨ المميزات

- رفع **ملفي Excel** منفصلين (قائمة A وقائمة B)
- اختيار **الشيت + العمود** من كل ملف بشكل مستقل
- تنظيف عميق بـ **18 قاعدة تطبيع** للنصوص العربية
- **4 مقاييس تشابه** (Jaro-Winkler + Token Sort + Token Set + Levenshtein) + درجة موزونة
- عرض **أفضل 3 مرشحين** لكل سجل
- **8 شيتات** في ملف الإخراج: أصل، منظّف، تطابقات، مراجعة بشرية، غير متطابقة، إحصائيات، خريطة صفوف

---

## 🚀 التشغيل محلياً (دقيقتان)

### المتطلبات
- Python 3.10 أو أحدث -> https://www.python.org/downloads/

### الخطوات

```bash
# 1) فك الضغط عن المشروع
unzip arabic-match-platform.zip
cd arabic-match-platform

# 2) إنشاء بيئة افتراضية (اختياري لكن موصى به)
python -m venv venv
source venv/bin/activate        # على macOS/Linux
venv\Scripts\activate           # على Windows

# 3) تثبيت المكتبات
pip install -r requirements.txt

# 4) تشغيل التطبيق
streamlit run app/streamlit_app.py

# 5) افتح المتصفح على:
# http://localhost:8501
```

---

## 📤 النشر على GitHub

### الخطوة 1: إنشاء مستودع جديد
1. ادخل على https://github.com/new
2. اسم المستودع: `arabic-match-platform`
3. اجعله **Public** (لتتمكن الاستضافة المجانية من قراءته)
4. **لا تضف** README أو .gitignore (لأنها موجودة هنا)

### الخطوة 2: رفع الملفات
ارفع محتويات مجلد `arabic-match-platform/` إلى المستودع بإحدى طريقتين:

**الطريقة A — من خلال الموقع (سهلة):**
1. على صفحة المستودع، اضغط **uploading an existing file** أو **Add file → Upload files**
2. اسحب وأفلت كل الملفات والمجلدات داخل المجلد الرئيسي:
   - `app/` كاملاً
   - `data/`
   - `requirements.txt`
   - `README.md`
   - `packages.txt`
   - `.gitignore`
3. اضغط **Commit changes**

**الطريقة B — من سطر الأوامر (للمستخدمين المتقدمين):**
```bash
cd arabic-match-platform
git init
git add .
git commit -m "Initial commit: Arabic lists matching platform"
git branch -M main
git remote add origin https://github.com/<اسم-المستخدم>/arabic-match-platform.git
git push -u origin main
```

### الخطوة 3: التحقق
افتح `https://github.com/<اسم-المستخدم>/arabic-match-platform` وتأكد ظهور جميع الملفات.

---

## 🌐 النشر كخدمة ويب عامة

بعد رفع الملفات على GitHub، يمكنك نشر التطبيق برابط عام مجّاني.

### الخيار 1: Streamlit Community Cloud (الأسهل — موصى به)

1. ادخل على https://share.streamlit.io بحساب GitHub نفسه
2. اضغط **New app**
3. املأ الحقول:
   - **Repository:** `<اسم-المستخدم>/arabic-match-platform`
   - **Branch:** `main`
   - **Main file path:** `app/streamlit_app.py`
4. اضغط **Deploy**
5. بعد 1-3 دقائق ستحصل على رابط مثل:
   `https://arabic-match-platform.streamlit.app`

> هذا هو الخيار الأبسط، متوقف على بنيان Streamlit الأصلي.

### الخيار 2: Render (خدمة Lifenet / Netlify البديلة للخوادم الديناميكية)

> **ملاحظة:** Netlify و Lifenet مهيآتان للمواقع الساكنة (Static Sites) و SPA، ولا تنصح بهما لتطبيق Streamlit الذي يحتاج خادم Python. إن كنت تقصد **Netlify**، فالخيار الأنسب لتطبيق بهذا الحجم هو **Streamlit Cloud** أو **Render**.

**على Render:**
1. ادخل بحساب GitHub على https://render.com
2. اضغط **New + → Web Service**
3. اربط المستودع `arabic-match-platform`
4. املأ:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
5. اضغط **Create Web Service**
6. بعد دقيقتين سيعطيك Render رابطاً عاماً مثل:
   `https://arabic-match-platform.onrender.com`

---

## 🧪 اختبر بعد النشر

استخدم الملفين داخل `data/samples/`:
- `list_A.xlsx` — قائمة 20 موظفاً بأخطاء إدخال واقعية
- `list_B.xlsx` — نفس الموظفين بأخطاء مختلفة

بعد التشغيل، جرّب:
1. ارفع الملفين
2. اختر شيت العمود + العمود المناسب
3. اضغط **ابدأ المعالجة والمطابقة**
4. نزّل ملف النتائج (8 شيتات)

---

## 🧱 هيكل المشروع

```
arabic-match-platform/
├── app/
│   ├── __init__.py
│   ├── normalizer.py       ← 18 قاعدة تطبيع عربية
│   ├── matcher.py          ← محرّك المطابقة (Jaro-Winkler + Token + Levenshtein)
│   ├── io_helpers.py       ← قراءة آمنة لـ Excel
│   ├── exporter.py         ← بناء ملف Excel الخرجي (8 شيتات)
│   └── streamlit_app.py    ← واجهة المستخدم الرئيسية (RTL)
├── data/
│   ├── samples/
│   │   ├── list_A.xlsx     ← ملف اختبار A
│   │   └── list_B.xlsx     ← ملف اختبار B
│   └── sample_output.xlsx  ← عيّنة من ملف نتائج
├── requirements.txt
├── packages.txt
├── .gitignore
└── README.md (هذا الملف)
```

---

## 📜 الترخيص

مصدر مفتوح — يمكنك استخدامه وتعديله بحرية.
