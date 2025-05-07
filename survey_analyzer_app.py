import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Survey Analyzer", layout="wide")
st.title("📊 Survey Response Analyzer")

uploaded_file = st.file_uploader("Upload your Excel file (.xlsx)", type="xlsx")

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet = st.selectbox("Select a sheet", xls.sheet_names)
    df = pd.read_excel(xls, sheet_name=sheet)

    column = st.selectbox("Select the column with responses", df.columns)
    st.markdown("🕵️ Preview of selected column:")
    st.write(df[column].dropna().head())
    raw_responses = df[column].dropna().astype(str).str.split(',')

    st.markdown("### Enter answer options (one per line, exact match):")
    raw_input = st.text_area("Example:\nSetting up devices\nManaging bills\nAccessing education")

    if raw_input:
        categories = [line.strip() for line in raw_input.split('\n') if line.strip()]
        counts = {cat: 0 for cat in categories}
        for row in raw_responses:
            cleaned = [a.strip() for a in row]
            for cat in categories:
                counts[cat] += cleaned.count(cat)

        total_with_dnk = sum(counts.values())
        dnk_label = "Not interested in any of these topics"
        total_without_dnk = sum(v for k, v in counts.items() if k != dnk_label)

        df_counts = pd.DataFrame(list(counts.items()), columns=["Answer Option", "Count"])
        df_counts["Percent"] = df_counts["Count"] / total_with_dnk * 100
        df_counts["Percent"] = df_counts["Percent"].round(1).astype(str) + "%"

        df_counts["Formatted"] = df_counts.apply(
            lambda row: f"{int(row['Count']):,} out of {total_with_dnk:,} respondents"
            if row["Answer Option"] != dnk_label else "", axis=1
        )

        total_row = pd.DataFrame([["Total (excluding 'Not interested')", total_without_dnk, "—", ""]], columns=df_counts.columns)
        total_row_all = pd.DataFrame([["Total (including 'Not interested')", total_with_dnk, "100.0%", ""]], columns=df_counts.columns)

        df_final = pd.concat([df_counts[df_counts["Answer Option"] != dnk_label],
                              total_row,
                              df_counts[df_counts["Answer Option"] == dnk_label],
                              total_row_all], ignore_index=True)

        st.markdown("### ✅ Results:")
        st.dataframe(df_final, use_container_width=True)

        def convert_df(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Results')
            return output.getvalue()

        excel_data = convert_df(df_final)
        st.download_button(
            label="📥 Download results as Excel",
            data=excel_data,
            file_name="survey_analysis_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

