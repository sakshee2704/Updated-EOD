# pdf_generator.py
import streamlit as st # Keep this import for potential future Streamlit-related messages
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import base64
from config import LOAN_TYPES # Import LOAN_TYPES from config

def generate_pdf_reports(df):
    """
    Generates End-of-Day PDF reports for each employee based on the provided DataFrame.
    Gracefully handles missing columns by substituting default values.
    Returns a tuple: (pdf_data_dictionary, list_of_warnings).
    """
    pdf_data = {}
    grouped = df.groupby("EmployeeID")
    today = datetime.today().strftime("%Y-%m-%d")

    # List to collect warnings related to data inconsistencies during PDF generation
    generation_warnings = []

    for emp_id, data in grouped:
        # Safely get EmployeeName and Branch, providing defaults if columns are missing
        # If 'EmployeeName' or 'Branch' are missing entirely from the DataFrame,
        # it would mean the initial df validation was too lenient.
        # But for safety, .get() is still good.
        name = data['EmployeeName'].iloc[0] if 'EmployeeName' in data.columns else "UNKNOWN EMPLOYEE"
        branch = data['Branch'].iloc[0] if 'Branch' in data.columns else "UNKNOWN BRANCH"

        # Safely get Amount for Debits and Credits
        total_debit = 0.0
        total_credit = 0.0
        if 'Amount' in data.columns and 'Type' in data.columns:
            total_debit = data[data['Type'] == 'Debit']['Amount'].sum()
            total_credit = data[data['Type'] == 'Credit']['Amount'].sum()
        else:
            generation_warnings.append(f"Employee {name} ({emp_id}): 'Amount' or 'Type' columns missing for transaction summary. Debits/Credits will show 0.")


        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, f"EOD Report - {name} ({emp_id})", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, f"Date: {today} | Branch: {branch}", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(60, 10, f"Total Debits: Rs {total_debit:.2f}", ln=False)
        pdf.cell(60, 10, f"Total Credits: Rs {total_credit:.2f}", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(60, 10, "Loan Type", border=1)
        pdf.cell(60, 10, "Paid", border=1)
        pdf.cell(60, 10, "Remaining", border=1)
        pdf.ln()
        pdf.set_font("Arial", "", 12)
        for loan in LOAN_TYPES:
            paid_col = f"{loan} Paid"
            remaining_col = f"{loan} Remaining"

            # Check if loan-specific columns exist before summing
            paid = data[paid_col].sum() if paid_col in data.columns else 0.0
            remaining = data[remaining_col].sum() if remaining_col in data.columns else 0.0

            if paid_col not in data.columns or remaining_col not in data.columns:
                generation_warnings.append(f"Employee {name} ({emp_id}): Loan details for '{loan}' missing one or both of '{paid_col}' and '{remaining_col}' columns. Showing 0 for missing values.")

            pdf.cell(60, 10, loan, border=1)
            pdf.cell(60, 10, f"Rs {paid:.2f}", border=1)
            pdf.cell(60, 10, f"Rs {remaining:.2f}", border=1)
            pdf.ln()

        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Transaction History", ln=True)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(40, 10, "Date", border=1)
        pdf.cell(30, 10, "Type", border=1)
        pdf.cell(40, 10, "Amount", border=1)
        pdf.cell(80, 10, "Description", border=1)
        pdf.ln()
        pdf.set_font("Arial", "", 11)

        # Check for existence of transaction columns for each row
        # This loop iterates over data which is already filtered for this employee
        # So we check columns within 'row' Series using .get()
        for _, row in data.iterrows():
            tx_date = str(row.get('Date', 'N/A'))
            tx_type = str(row.get('Type', 'N/A'))
            tx_amount = f"Rs {row.get('Amount', 0.0):.2f}"
            tx_description = str(row.get('Description', 'N/A'))[:40]

            # Add warnings if specific columns for transactions are missing for this row
            # Note: These specific 'per-row' warnings might become very verbose if many rows are affected.
            # The initial DataFrame validation should ideally catch most critical missing columns at the file level.
            if 'Date' not in row: generation_warnings.append(f"Employee {name} ({emp_id}) transaction missing 'Date' in a row. Using 'N/A'.")
            if 'Type' not in row: generation_warnings.append(f"Employee {name} ({emp_id}) transaction missing 'Type' in a row. Using 'N/A'.")
            if 'Amount' not in row: generation_warnings.append(f"Employee {name} ({emp_id}) transaction missing 'Amount' in a row. Using 0.0.")
            if 'Description' not in row: generation_warnings.append(f"Employee {name} ({emp_id}) transaction missing 'Description' in a row. Using 'N/A'.")


            pdf.cell(40, 10, tx_date, border=1)
            pdf.cell(30, 10, tx_type, border=1)
            pdf.cell(40, 10, tx_amount, border=1)
            pdf.cell(80, 10, tx_description, border=1)
            pdf.ln()

        filename = f"EOD_Report_{emp_id}_{today}.pdf"
        pdf.output(filename)

        with open(filename, "rb") as f:
            pdf_bytes = f.read()
        os.remove(filename)

        pdf_data[emp_id] = {
            "filename": filename,
            "name": name,
            "branch": branch,
            "pdf_bytes": pdf_bytes
        }

    # Remove duplicate warnings before returning
    unique_warnings = list(set(generation_warnings))
    return pdf_data, unique_warnings

def display_pdf(pdf_bytes, filename):
    """
    Encodes PDF bytes to base64 and displays them in an iframe for preview,
    along with a download button.
    """
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400px" type="application/pdf"></iframe>'
    st.markdown(f"### {filename}", unsafe_allow_html=True)
    st.markdown(pdf_display, unsafe_allow_html=True)
    st.download_button(label="Download PDF", data=pdf_bytes, file_name=filename, mime='application/pdf')
