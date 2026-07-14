"""
التطبيق الرئيسي لتطابق القوائم العربية.
Streamlit UI + معالجة كاملة + تصدير Excel متعدد الشيتات.
"""
import sys
import io
from pathlib import Path

# إضافة الـ app إلى المسار
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR.parent))

import streamlit as st
import pandas as pd
import numpy as np

from app.normalizer import normalize_arabic, summarize_changes, normalize_column
from app.matcher import similarity_score, classify, match_lists
from app.io_helpers import read_excel_safe, list_sheets, list_columns, preview
from app.exporter import build_output_workbook


# ─────────────────── إعدادات الصفحة ───────────────────
st.set_page_config(
    page_title="منصة مطابقة القوائم العربية",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS مخصص لدعم العربية واتجاه RTL
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, h4, h5, h6, p, li, label, div, span { text-align: right; }
    .stDataFrame { direction: rtl; }
    div[data-testid="stMarkdownContainer"] { text-align: right; }
    .metric-card { background: linear-gradient(135deg, #1F4E78, #2E86AB);
                   color: white; padding: 1rem; border-radius: 10px;
                   text-align: center; }
</style>
""", unsafe_allow_html=True)


# ─────────────────── العنوان ───────────────────
st.title("🔍 منصة مطابقة القوائم العربية")
st.markdown("""
**منظومة كاملة لتنظيف وتطبيع ومطابقة أعمدة عربية من ملفين Excel**

المميزات:
- رفع ملفين Excel (xlsx / xls)
- اختيار الشيت والعمود من كل ملف بشكل مستقل
- تنظيف عميق للنصوص العربية (18 قاعدة تطبيع)
- 4 مقاييس تشابه + درجة موزونة + أفضل 3 مرشحين
- ملف Excel خرجي يحوي شيت للأصل، شيت للمنظّف، شيت للتطابقات، شيت للمراجعة، شيت للإحصائيات، شيت لخريطة الصفوف
""")


# ─────────────────── رفع الملفين ───────────────────
st.header("📤 الخطوة 1: رفع الملفين")
col1, col2 = st.columns(2)

with col1:
    file_a = st.file_uploader(
        "📄 الملف الأول (القائمة A)",
        type=["xlsx", "xls"],
        key="file_a",
        help="ارفع ملف Excel يحوي القائمة الأولى"
    )

with col2:
    file_b = st.file_uploader(
        "📄 الملف الثاني (القائمة B)",
        type=["xlsx", "xls"],
        key="file_b",
        help="ارفع ملف Excel يحوي القائمة الثانية"
    )


# ─────────────────── اختيار الشيتات والأعمدة ───────────────────
if file_a and file_b:
    st.header("📋 الخطوة 2: اختيار الشيت والعمود")

    # قراءة أسماء الشيتات
    sheets_a = list_sheets(file_a)
    sheets_b = list_sheets(file_b)

    col_a_sel, col_b_sel = st.columns(2)

    with col_a_sel:
        st.subheader("📄 الملف A")
        sheet_a_name = st.selectbox("اختر الشيت", sheets_a, key="sheet_a")

    with col_b_sel:
        st.subheader("📄 الملف B")
        sheet_b_name = st.selectbox("اختر الشيت", sheets_b, key="sheet_b")

    # قراءة الأعمدة بعد اختيار الشيت
    file_a.seek(0)
    file_b.seek(0)
    df_a_raw = read_excel_safe(file_a, sheet_name=sheet_a_name)
    df_b_raw = read_excel_safe(file_b, sheet_name=sheet_b_name)

    cols_a = list_columns(df_a_raw)
    cols_b = list_columns(df_b_raw)

    col_a_col, col_b_col = st.columns(2)

    with col_a_col:
        col_a = st.selectbox("اختر عمود المقارنة من الملف A", cols_a, key="col_a")

    with col_b_col:
        col_b = st.selectbox("اختر عمود المقارنة من الملف B", cols_b, key="col_b")

    # ─────────────────── معاينة سريعة ───────────────────
    with st.expander("👀 معاينة البيانات الأولية"):
        p1, p2 = st.columns(2)
        with p1:
            st.markdown("**الملف A (الأول):**")
            st.dataframe(preview(df_a_raw[[col_a]].rename(columns={col_a: col_a}),
                                 10), use_container_width=True)
        with p2:
            st.markdown("**الملف B (الثاني):**")
            st.dataframe(preview(df_b_raw[[col_b]].rename(columns={col_b: col_b}),
                                 10), use_container_width=True)


    # ─────────────────── إعدادات المطابقة ───────────────────
    st.header("⚙️ الخطوة 3: إعدادات المطابقة")
    col_set1, col_set2, col_set3 = st.columns(3)

    with col_set1:
        threshold_hi = st.slider("عتبة التطابق التام", 70, 100, 90, 1)
    with col_set2:
        threshold_lo = st.slider("عتبة المراجعة البشرية", 40, threshold_hi - 1, 70, 1)
    with col_set3:
        drop_tokens = st.checkbox("حذف الكلمات الشائعة (بن/ابن/السيد)", value=False)


    # ─────────────────── زر التشغيل ───────────────────
    st.header("🚀 الخطوة 4: تشغيل المطابقة")

    if st.button("▶️ ابدأ المعالجة والمطابقة", type="primary", use_container_width=True):
        with st.spinner("⏳ جارٍ تنظيف ومطابقة البيانات..."):
            # تنظيف العمودين
            df_a_clean = df_a_raw.copy()
            df_a_clean["_normalized"] = normalize_column(df_a_clean[col_a], drop_tokens)
            df_a_clean[col_a + "_منظّف"] = df_a_clean["_normalized"]
            df_a_clean["أسباب_التغيير"] = [
                summarize_changes(a, c)
                for a, c in zip(df_a_raw[col_a].astype(str), df_a_clean["_normalized"].astype(str))
            ]

            df_b_clean = df_b_raw.copy()
            df_b_clean["_normalized"] = normalize_column(df_b_clean[col_b], drop_tokens)
            df_b_clean[col_b + "_منظّف"] = df_b_clean["_normalized"]
            df_b_clean["أسباب_التغيير"] = [
                summarize_changes(a, c)
                for a, c in zip(df_b_raw[col_b].astype(str), df_b_clean["_normalized"].astype(str))
            ]

            # مطابقة
            df_match, df_no_match, stats = match_lists(
                df_a_clean, col_a,
                df_b_clean, col_b,
            )

            # إعادة تطبيق العتبة المخصصة
            df_match["الحالة"] = df_match["درجة_التشابه"].apply(
                lambda s: classify(s, threshold_hi, threshold_lo)
            )

            st.session_state["results"] = {
                "df_a_raw": df_a_raw,
                "df_b_raw": df_b_raw,
                "df_a_clean": df_a_clean,
                "df_b_clean": df_b_clean,
                "df_match": df_match,
                "df_no_match": df_no_match,
                "stats": stats,
                "col_a": col_a,
                "col_b": col_b,
                "sheet_a": sheet_a_name,
                "sheet_b": sheet_b_name,
            }

        st.success(f"✅ تمت المعالجة! إجمالي السجلات: {stats['الإجمالي_A']}")


# ─────────────────── عرض النتائج ───────────────────
if "results" in st.session_state:
    r = st.session_state["results"]
    stats = r["stats"]

    st.header("📊 النتائج")

    # بطاقات الإحصائيات
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("إجمالي سجلات A", stats.get("الإجمالي_A", 0))
    with c2:
        st.metric("✅ تطابق تام", stats.get("تام", 0))
    with c3:
        st.metric("⚠️ مراجعة بشرية", stats.get("مراجعة", 0))
    with c4:
        st.metric("❌ بدون تطابق", stats.get("بدون", 0))

    st.metric("نسبة التطابق التام", f"{stats.get('نسبة_التطابق_التام', 0)} %")

    # شيت النتائج
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 التطابقات المرتبة",
        "⚠️ تحتاج مراجعة بشرية",
        "❌ غير المتطابقة",
        "🧹 البيانات المنظفة",
    ])

    with tab1:
        st.dataframe(
            r["df_match"].sort_values("درجة_التشابه", ascending=False),
            use_container_width=True, height=500,
        )
    with tab2:
        review_df = r["df_match"][
            r["df_match"]["الحالة"].str.contains("مراجعة", na=False)
        ].sort_values("درجة_التشابه", ascending=False)
        st.dataframe(review_df, use_container_width=True, height=500)
    with tab3:
        st.dataframe(r["df_no_match"], use_container_width=True, height=500)
    with tab4:
        ca, cb = st.columns(2)
        with ca:
            st.markdown("**البيانات المنظّفة - الملف A**")
            st.dataframe(
                r["df_a_clean"][[col_name for col_name in [r["col_a"],
                                                            r["col_a"] + "_منظّف",
                                                            "أسباب_التغيير"]
                                   if col_name in r["df_a_clean"].columns]],
                use_container_width=True, height=500,
            )
        with cb:
            st.markdown("**البيانات المنظّفة - الملف B**")
            st.dataframe(
                r["df_b_clean"][[col_name for col_name in [r["col_b"],
                                                            r["col_b"] + "_منظّف",
                                                            "أسباب_التغيير"]
                                   if col_name in r["df_b_clean"].columns]],
                use_container_width=True, height=500,
            )

    # ─────────────────── تنزيل الإكسل ───────────────────
    st.header("💾 الخطوة 5: تنزيل ملف النتائج")

    with st.spinner("⏳ جارٍ بناء ملف Excel..."):
        xlsx_bytes = build_output_workbook(
            df_a_raw=r["df_a_raw"],
            df_b_raw=r["df_b_raw"],
            df_a_clean=r["df_a_clean"],
            df_b_clean=r["df_b_clean"],
            df_match=r["df_match"],
            df_no_match=r["df_no_match"],
            stats=r["stats"],
            col_a=r["col_a"],
            col_b=r["col_b"],
            sheet_a=r["sheet_a"],
            sheet_b=r["sheet_b"],
        )

    st.download_button(
        label="⬇️ تنزيل ملف النتائج (Excel متعدد الشيتات)",
        data=xlsx_bytes,
        file_name=f"arabic_match_results_{r['sheet_a']}_{r['sheet_b']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )

    st.info("""
    📋 **الشيتات في الملف الخرجي:**
    1. الأصل_A — البيانات الخام للملف الأول
    2. الأصل_B — البيانات الخام للملف الثاني
    3. البيانات_المنظفة_A — مع عمود "أسباب التغيير"
    4. البيانات_المنظفة_B — مع عمود "أسباب التغيير"
    5. التطابقات — كل تفاصيل المطابقة + أفضل 3 مرشحين
    6. غير_المتطابقة — سجلات A بلا تطابق
    7. الإحصائيات — ملخص شامل
    8. خريطة_الصفوف — ربط صف الأصل بالصف المنظّف في كلا الملفين
    """)
