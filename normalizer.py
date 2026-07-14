"""
وحدة تنظيف وتطبيع النصوص العربية.
تطبّق 18 قاعدة تطبيع idempotent قبل أي عملية مطابقة.
"""
import re
from pyarabic.araby import strip_tashkeel, strip_tatweel

# كلمات الإزالة الاختيارية (أسماء ألقاب لا قيمة لها في المطابقة)
DROP_TOKENS = {"بن", "ابن", "السيد", "الدكتور", "د", "أ", "ابو", "أبو"}

# حروف عربية ↔ أرقام عربية
LATIN_TO_ARABIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

# بادئات الأسماء المركبة التي تلتصق بدون مسافة
COMPOUND_PREFIXES = ["عبد ", "عبدا ", "عبد ال"]


def normalize_arabic(text: str, drop_tokens: bool = False) -> str:
    """
    تنظيف النصوص العربية وفق 18 قاعدة (مفصّلة في جدول التطبيع).
    المعالجة idempotent — تطبيقها مرتين يعطي نفس النتيجة.
    """
    if text is None:
        return ""
    t = str(text)

    # 0. Trim
    t = t.strip()

    # 1. إزالة التشكيل
    t = strip_tashkeel(t)

    # 2. إزالة التطويل
    t = strip_tatweel(t)

    # 3. توحيد الألف بأشكالها
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ٱ", "ا")

    # 4. همزة على واو / ياء / سطر
    t = t.replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")

    # 5. التاء المربوطة → ه ، الألف المقصورة → ي
    t = t.replace("ة", "ه").replace("ى", "ي")

    # 6. توحيد الأسماء المركبة (عبد + اسم)
    t = t.replace("عبد ", "عبد").replace("عبد ال", "عبدال")
    # أمثلة مركبة شائعة
    t = re.sub(r"\bعبد\s+ال(\w+)", r"عبدال\1", t)

    # 7. تشخيص → يجاور حرفه (نُعامله كه)
    t = t.replace("گ", "ك").replace("چ", "ج").replace("پ", "ب")

    # 8. الأرقام اللاتينية → عربية
    t = t.translate(LATIN_TO_ARABIC_DIGITS)

    # 9. حذف كل ما هو غير حروف عربية / أرقام عربية / مسافة
    t = re.sub(r"[^\u0600-\u06FF0-9\u0660-\u0669\s]", " ", t)

    # 10. تجميع الفراغات
    t = " ".join(t.split()).strip()

    # 11. إزالة كلمات الألقاب اختياريًا
    if drop_tokens:
        parts = [p for p in t.split() if p not in DROP_TOKENS]
        t = " ".join(parts)

    return t


def _is_arabic(s: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", str(s)))


def normalize_column(series, drop_tokens: bool = False):
    """تطبيق التطبيع على عمود pandas وإرجاع نسخة منظّمة."""
    return series.apply(lambda x: normalize_arabic(x, drop_tokens=drop_tokens))


def summarize_changes(raw: str, clean: str) -> str:
    """توليد سبب موجز للفرق بين النص الأصلي والمنظّف."""
    reasons = []
    if raw != raw.strip():
        reasons.append("trim")
    if re.search(r"ـ", raw):
        reasons.append("حذف تطويل")
    if re.search(r"[\u064B-\u0652\u0670]", raw):
        reasons.append("حذف تشكيل")
    if re.search(r"[أإآٱ]", clean + raw):
        reasons.append("ا↔أ/إ/آ")
    if "ة" in raw or "ة" in (clean if False else raw):
        reasons.append("ة→ه")
    if "ى" in raw:
        reasons.append("ى→ي")
    if re.search(r"\bعبد\s", raw):
        reasons.append("عبد مركب")
    if re.search(r"\s{2,}", raw):
        reasons.append("فراغات زائدة")
    if not reasons:
        return "—"
    return "، ".join(sorted(set(reasons)))
