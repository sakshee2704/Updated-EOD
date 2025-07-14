from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

def get_column(df, col_name):
    for col in df.columns:
        if col.lower() == col_name.lower():
            return col
    return None

def generate_pdf_for_employee(emp_data, filepath):
    print("Columns in emp_data:", emp_data.columns.tolist())
    
    emp_id_col = get_column(emp_data, 'EmployeeID')
    amount_col = get_column(emp_data, 'Amount')
    type_col = get_column(emp_data, 'Type')
    dept_col = get_column(emp_data, 'Category') or get_column(emp_data, 'Branch')
    
    if not all([emp_id_col, amount_col, type_col, dept_col]):
        raise KeyError(f"Missing one of the required columns. Found columns: {emp_data.columns.tolist()}")
    
    emp_id = emp_data[emp_id_col].iloc[0]
    
    # Calculate total credit and debit based on Type column
    total_credit = emp_data.loc[emp_data[type_col].str.lower() == 'credit', amount_col].sum()
    total_debit = emp_data.loc[emp_data[type_col].str.lower() == 'debit', amount_col].sum()
    
    loan_departments = emp_data[dept_col].nunique()
    
    styles = getSampleStyleSheet()
    content = [
        Paragraph(f"<b>End of the Day Report</b>", styles['Title']),
        Spacer(1, 12),
        Paragraph(f"<b>Employee ID:</b> {emp_id}", styles['Heading2']),
        Paragraph(f"<b>Total Credit:</b> ₹{total_credit}", styles['Normal']),
        Paragraph(f"<b>Total Debit:</b> ₹{total_debit}", styles['Normal']),
        Paragraph(f"<b>Loan from Departments:</b> {loan_departments}", styles['Normal']),
        Spacer(1, 12),
        Paragraph("<b>Transaction Details:</b>", styles['Heading3']),
        Spacer(1, 6)
    ]

    for _, row in emp_data.iterrows():
        line = ', '.join([f"{col}: {row[col]}" for col in emp_data.columns])
        content.append(Paragraph(line, styles['Normal']))
        content.append(Spacer(1, 6))

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    doc.build(content)
