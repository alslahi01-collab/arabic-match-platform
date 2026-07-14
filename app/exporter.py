"""
مولّد ملف Excel الخرجي متعدد الشيتات.
"""
import pandas as pd
from datetime import datetime


def build_output_workbook(
    df_a_raw: pd.DataFrame,
    df_b_raw: pd.DataFrame,
    df_a_clean: pd.DataFrame,
    df_b_clean: pd.DataFrame,
    df_match: pd.DataFrame,
    df_no_match: pd.DataFrame,
    stats: dict,
    col_a: str,
    col_b: str,
    sheet_a: str,
    sheet_b: str,
) -> bytes:
    """
    يبني ملف Excel يحوي:
    1) الأصل_A
    2) الأصل_B
    3) البيانات_المنظفة_A (مع خانة أسباب التغيير)
    4) البيانات_المنظفة_B
    5) التطابقات (مع كل المقاييس + أفضل 3 مرشحين + الحالة)
    6) غير_المتطابقة
    7) الإحصائيات
    8) خريطة_الصفوف (ربط الصفوف الأصلية بالمنظفة)
    """
    import io
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # 1) الأصل
        df_a_raw.to_excel(writer, sheet_name="الأصل_A", index=False)
        df_b_raw.to_excel(writer, sheet_name="الأصل_B", index=False)

        # 2) البيانات المنظفة (مع عمود أسباب)
        from .normalizer import summarize_changes
        clean_a = df_a_clean.copy()
        clean_a["أسباب_التغيير"] = [
            summarize_changes(a, c) for a, c in zip(
                df_a_raw[col_a].astype(str), clean_a[col_a].astype(str)
            )
        ]
        clean_a.to_excel(writer, sheet_name="البيانات_المنظفة_A", index=False)

        clean_b = df_b_clean.copy()
        clean_b["أسباب_التغيير"] = [
            summarize_changes(a, c) for a, c in zip(
                df_b_raw[col_b].astype(str), clean_b[col_b].astype(str)
            )
        ]
        clean_b.to_excel(writer, sheet_name="البيانات_المنظفة_B", index=False)

        # 3) التطابقات
        if df_match.empty:
            pd.DataFrame({"ملاحظة": ["لا توجد تطابقات وفق العتبة الحالية"]}).to_excel(
                writer, sheet_name="التطابقات", index=False
            )
        else:
            df_match.to_excel(writer, sheet_name="التطابقات", index=False)

        # 4) غير المتطابقة
        if df_no_match.empty:
            pd.DataFrame({"ملاحظة": ["جميع السجلات لها تطابق"]}).to_excel(
                writer, sheet_name="غير_المتطابقة", index=False
            )
        else:
            df_no_match.to_excel(writer, sheet_name="غير_المتطابقة", index=False)

        # 5) الإحصائيات
        stats_rows = [
            ("الشيت A", sheet_a),
            ("الشيت B", sheet_b),
            ("عمود المقارنة A", col_a),
            ("عمود المقارنة B", col_b),
            ("تاريخ التشغيل", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("──── إجماليات ────", ""),
            ("إجمالي سجلات A", stats.get("الإجمالي_A", 0)),
            ("تطابق تام (≥90)", stats.get("تام", 0)),
            ("مراجعة بشرية (70-89)", stats.get("مراجعة", 0)),
            ("بدون تطابق (<70)", stats.get("بدون", 0)),
            ("نسبة التطابق التام %", stats.get("نسبة_التطابق_التام", 0)),
        ]
        pd.DataFrame(stats_rows, columns=["المؤشر", "القيمة"]).to_excel(
            writer, sheet_name="الإحصائيات", index=False
        )

        # 6) خريطة الصفوف (Mapping) — تربط الصفوف في الأصل بالمنظف
        mapping_a = pd.DataFrame({
            "رقم_الصف": list(range(len(df_a_raw))),
            "الأصلي": df_a_raw[col_a].astype(str),
            "المنظّف": clean_a[col_a].astype(str),
        })
        mapping_b = pd.DataFrame({
            "رقم_الصف": list(range(len(df_b_raw))),
            "الأصلي": df_b_raw[col_b].astype(str),
            "المنظّف": clean_b[col_b].astype(str),
        })
        # نضعهما جنباً إلى جنب
        max_len = max(len(mapping_a), len(mapping_b))
        mapping_a = mapping_a.reindex(range(max_len))
        mapping_b = mapping_b.reindex(range(max_len))
        map_df = pd.DataFrame({
            "رقم_A": mapping_a["رقم_الصف"],
            "الأصلي_A": mapping_a["الأصلي"],
            "المنظّف_A": mapping_a["المنظّف"],
            "رقم_B": mapping_b["رقم_الصف"],
            "الأصلي_B": mapping_b["الأصلي"],
            "المنظّف_B": mapping_b["المنظّف"],
        })
        map_df.to_excel(writer, sheet_name="خريطة_الصفوف", index=False)

        # تنسيق الأعمدة في ملف الإخراج
        _format_workbook(writer, df_a_raw, df_b_raw, clean_a, clean_b, df_match)

    return output.getvalue()


def _format_workbook(writer, df_a_raw, df_b_raw, clean_a, clean_b, df_match):
    """تنسيق عرض الأعمدة + تجميد الصف الأول + RTL."""
    wb = writer.book

    # تنسيق الرأس
    header_fmt = wb.add_format({
        "bold": True, "bg_color": "#1F4E78", "font_color": "white",
        "align": "center", "valign": "vcenter", "border": 1,
    })
    cell_fmt = wb.add_format({"text_wrap": True, "valign": "top"})

    # ضبط عرض الأعمدة + RTL في كل الشيتات
    for ws_name in writer.sheets.values():
        ws = ws_name
        # RTL + قراءة من اليمين لليسار
        ws.right_to_left()
        ws.set_row(0, 25, header_fmt)
        ws.freeze_panes(1, 0)
