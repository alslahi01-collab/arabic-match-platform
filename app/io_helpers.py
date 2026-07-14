"""
مساعدات قراءة/كتابة Excel بأمان.
"""
from __future__ import annotations
import pandas as pd
from typing import Dict, List


def read_excel_safe(path_or_buffer, sheet_name: str | int | None = 0) -> pd.DataFrame:
    """قراءة آمنة لملف/مسار إكسل. الإرجاع: DataFrame."""
    df = pd.read_excel(path_or_buffer, sheet_name=sheet_name, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    # ملء الخانات الفارغة صراحة
    df = df.fillna("")
    return df


def list_sheets(path_or_buffer) -> List[str]:
    """إرجاع أسماء الشيتات في ملف إكسل."""
    xl = pd.ExcelFile(path_or_buffer)
    return xl.sheet_names


def list_columns(df: pd.DataFrame) -> List[str]:
    """قائمة بأسماء الأعمدة."""
    return [str(c) for c in df.columns]


def preview(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """عرض أول n صفوف."""
    return df.head(n).copy()
