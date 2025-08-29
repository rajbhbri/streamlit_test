import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import altair as alt
import matplotlib.pyplot as plt
import json
from datetime import datetime
import pyodbc
import openpyxl
import xlsxwriter
import plotly.express as px


# ---------- DATABASE CONNECTION ----------
def get_connection(host, dbname, Source_user, Source_pass):

    try:
        engine = create_engine(
            f"mssql+pyodbc://@{host}/{dbname}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")
        return engine
    except Exception as e:
        raise e


# ---------- DATA FETCH ----------
def fetch_data_col(engine, table, col):
    query = f"SELECT {col} FROM {table}"

    return pd.read_sql(query, engine)


# ---------- DATA VALIDATION ----------

def validate_data_cols(df1, df2):

    df1_cols = df1.columns.tolist()
    df2_cols = df2.columns.tolist()

    df1_col_len = len(df1_cols)
    df2_col_len = len(df2_cols)

    with pd.ExcelWriter('Column_Validations.xlsx', engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Sheet1')
        writer.sheets['Sheet1'] = worksheet
        start_row = 0
        for i in range(len(df1_cols)):
            col1 = df1_cols[i]

            # Count occurrences of each value
            count1 = df1[col1].value_counts().reset_index()
            count1.columns = [col1, 'Source_Count']

            if i < df2_col_len:
                col2 = df2_cols[i]
                count2 = df2[col2].value_counts().reset_index()
                count2.columns = [col2, 'Target_Count']
                # Merge the counts, keeping all possible groups
                comparison = pd.merge(count1, count2, on=col1, how='outer').fillna(0)
                # Convert counts to integers (optional)
                comparison['Source_Count'] = comparison['Source_Count'].astype(int)
                comparison['Target_Count'] = comparison['Target_Count'].astype(int)
                comparison['MATCH'] = comparison['Source_Count'] == comparison['Target_Count']
            else:
                comparison = count1

            # Write df title and data
            if i == 0:
                worksheet.write(0, 0, col1)
                comparison.to_excel(writer, sheet_name='Sheet1', startrow=1, startcol=0, index=False)
                start_row = len(comparison) + 3
                ##print(start_row)
            else:
                worksheet.write(start_row, 0, col1)
                comparison.to_excel(writer, sheet_name='Sheet1', startrow=start_row + 1, startcol=0, index=False)
                start_row = start_row + len(comparison) + 3
                ##print(start_row)

    return comparison


#----------Run Validation----------------

#def run_validation():
#    engine1_t = get_connection("WPF4XA0Y7\\SQLEXPRESS", "cLA")
    #    engine2_t = get_connection("WPF4XA0Y7\\SQLEXPRESS", "cLA")

    #    df1 = fetch_data(engine1_t, "[dbo].[IP]")
    #    df2 = fetch_data(engine2_t, "[dbo].[IP_Test]")

#   validate_data_cols(df1, df2)


#run_validation()

# ---------- STREAMLIT DASHBOARD ----------
st.markdown(
    """
    <style>
    body, p, div, h1, h2, h3, h4, h5, h6 {
        color: #00008B; /* Dark Blue */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(page_title="DB Validation Dashboard", layout="wide")
st.header('Professional Services')
st.title("Data Validation Dashboard (SDB vs TDB)")


with st.sidebar:
    st.header("Source DB Connection")
    Source_type = st.selectbox("Source Type", ["postgresql", "mysql", "mssql"])
    Source_host = st.text_input("Source Host", "localhost")
    Source_name = st.text_input("Source DB Name")
    Source_user = st.text_input("Source Username")
    Source_pass = st.text_input("Source Password", type="password")
    Source_table = st.text_input("Source Table")
    Source_column = st.text_input("Source Column")

    st.header("Target DB Connection")
    Target_type = st.selectbox("Target Type", ["postgresql", "mysql", "mssql"], key="Target")
    Target_host = st.text_input("Target Host", "localhost", key="host2")
    Target_name = st.text_input("Target DB Name", key="name2")
    Target_user = st.text_input("Target Username", key="user2")
    Target_pass = st.text_input("Target Password", type="password", key="pass2")
    Target_table = st.text_input("Target Table", key="table2")
    Target_column = st.text_input("Target Column")


if st.button("Run Validation"):
    try:
        st.info("Connecting to databases and fetching data...")
        engine1 = get_connection(Source_host, Source_name, Source_user, Source_pass)
        engine2 = get_connection(Target_host, Target_name, Target_user, Target_pass)

        df1 = fetch_data_col(engine1, Source_table, Source_column)
        df2 = fetch_data_col(engine2, Target_table, Target_column)

        st.success("Data fetched successfully! Running validation...")

        results = validate_data_cols(df1, df2)

        # Color cell green if value >= 50, else red
        styled_df = results.style.map(
            lambda x: f"background-color: {'green' if x is True else 'red'}", subset='MATCH'
        )

        st.subheader("Validation Summary")
        st.dataframe(styled_df)



        # st.subheader("Column-Level Mismatch Summary")
        # col_mismatches = pd.DataFrame.from_dict(results["Column Mismatches"], orient='index',
        #                                        columns=["Mismatch Count"])
        # st.dataframe(col_mismatches)
        # Export Button
        # if st.button("📁 Export Validation Report to Excel"):
        #    excel_file = export_to_excel(df1, df2, results)
        #    st.success(f"Validation report saved as: {excel_file}")
        #    with open(excel_file, "rb") as f:
        #        st.download_button("Download Excel Report", f, file_name=excel_file)


    except Exception as e:
        st.error(f"Error: {e}")