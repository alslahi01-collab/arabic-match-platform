"""
محرك المطابقة التقريبية للنصوص العربية المنظّفة.
يجمع 3 مقاييس من rapidfuzz ويصدر درجة موزونة نهائية.
"""
from rapidfuzz import fuzz
import pandas as pd


def similarity_score(a_norm: str, b_norm: str) -> dict:
    """حساب 3 مقاييس تشابه + الدرجة النهائية."""
    if not a_norm or not b_norm:
        return {
            "jaro_winkler": 0.0,
            "token_sort": 0.0,
            "token_set": 0.0,
            "final": 0.0,
        }
    jw = fuzz.WRatio(a_norm, b_norm)               # يعادل Jaro-Winkler مع تعديل للأسماء
    ts = fuzz.token_sort_ratio(a_norm, b_norm)     # يحلّ ترتيب الاسم/اللقب
    tse = fuzz.token_set_ratio(a_norm, b_norm)     # يتعامل مع الاسم المركب
    # يمكن إضافة Levenshtein عبر fuzz.ratio
    lev = fuzz.ratio(a_norm, b_norm)

    # المتوسط الموزون
    final = round(0.30 * jw + 0.25 * ts + 0.25 * tse + 0.20 * lev, 2)
    return {
        "jaro_winkler": round(jw, 2),
        "token_sort": round(ts, 2),
        "token_set": round(tse, 2),
        "levenshtein": round(lev, 2),
        "final": final,
    }


def classify(score: float, hi: int = 90, lo: int = 70) -> str:
    """تصنيف الحالة وفق العتبة."""
    if score >= hi:
        return "✅ تطابق تام"
    if score >= lo:
        return "⚠️ مراجعة بشرية"
    return "❌ بدون تطابق"


def match_lists(df_a: pd.DataFrame, col_a: str,
                df_b: pd.DataFrame, col_b: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    مطابقة كل سجل في A مع أفضل 3 مرشحين من B.
    يعيد: (جدول المطابقات، جدول عدم التطابق، إحصائيات)
    """
    a_norm = df_a["_normalized"].tolist()
    b_norm = df_b["_normalized"].tolist()
    b_orig = df_b[col_b].tolist()

    matches = []
    no_match = []

    # إحصائيات
    stats = {"تام": 0, "مراجعة": 0, "بدون": 0}

    for idx, (raw_a, clean_a) in enumerate(zip(df_a[col_a].tolist(), a_norm)):
        # حساب التشابه مع كل سجل في B
        scores = []
        for j, b in enumerate(b_norm):
            sc = similarity_score(clean_a, b)
            scores.append((j, b_orig[j], b, sc["final"], sc["jaro_winkler"],
                           sc["token_sort"], sc["token_set"], sc["levenshtein"]))

        # ترتيب تنازلي + حذف التكرارات
        scores.sort(key=lambda x: x[3], reverse=True)
        # إزالة السجلات التي تطابقت بالفعل (لتجنب تكرار التعيين)
        used_b = set()
        top3 = []
        for s in scores:
            if s[0] not in used_b:
                top3.append(s)
                used_b.add(s[0])
            if len(top3) == 3:
                break

        best = top3[0] if top3 else None
        if best is None or best[3] < 50:
            no_match.append({
                "رقم_الصف": idx,
                "الاسم_الأصلي_A": raw_a,
                "الاسم_المنظّف_A": clean_a,
                "السبب": "لا توجد مرشحات قوية",
            })
            stats["بدون"] += 1
            continue

        status = classify(best[3])
        if "تام" in status:
            stats["تام"] += 1
        elif "مراجعة" in status:
            stats["مراجعة"] += 1
        else:
            stats["بدون"] += 1

        # الصف الأساسي = أفضل تطابق
        matches.append({
            "رقم_صف_A": idx,
            "الأصلي_A": raw_a,
            "المنظّف_A": clean_a,
            "أفضل_تطابق_الأصلي_B": best[1],
            "أفضل_تطابق_المنظّف_B": best[2],
            "درجة_التشابه": best[3],
            "Jaro_Winkler": best[4],
            "Token_Sort": best[5],
            "Token_Set": best[6],
            "Levenshtein": best[7],
            "الحالة": status,
            "المرشح_الثاني": f"{top3[1][1]} ({top3[1][3]})" if len(top3) > 1 else "—",
            "المرشح_الثالث": f"{top3[2][1]} ({top3[2][3]})" if len(top3) > 2 else "—",
        })

    df_match = pd.DataFrame(matches)
    df_no = pd.DataFrame(no_match)

    # إحصائيات سريعة
    total_a = len(df_a)
    stats["الإجمالي_A"] = total_a
    stats["نسبة_التطابق_التام"] = round(stats["تام"] / total_a * 100, 2) if total_a else 0

    return df_match, df_no, stats
