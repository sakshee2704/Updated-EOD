# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import re

# Import functions and constants from our new modules
from config import LOAN_TYPES
from session_state_manager import initialize_session_state, reset_application_state, reset_file_related_state
from pdf_generator import generate_pdf_reports, display_pdf
from email_sender import send_email_report, validate_emails


# --- Page Configuration ---
st.set_page_config(
    page_title="EOD Banking Report Generator",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Attractive & Dynamic UI ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --primary-color: #2F80ED; /* A deep blue */
        --secondary-color: #28a745; /* Green for success */
        --accent-color: #FFC107; /* Amber for warnings */
        --danger-color: #DC3545; /* Red for errors */
        --background-color: #F8F9FA; /* Light grey background */
        --card-background: #FFFFFF; /* White card background */
        --text-color: #343A40; /* Dark grey text */
        --light-text-color: #6C757D; /* Lighter grey text */
        --border-color: #DEE2E6; /* Light border */
        --border-radius: 0.75rem; /* Rounded corners */
        --shadow: rgba(0, 0, 0, 0.08) 0px 4px 12px; /* Soft shadow */
    }

    body {
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
        background-color: var(--background-color);
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color);
        font-weight: 600;
    }

    /* General container styling for better visual separation */
    .stApp {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    /* Customizing Streamlit widgets */
    div[data-testid="stFileUploader"] > label {
        color: var(--text-color);
        font-size: 1.1em;
        font-weight: 500;
    }
    div[data-testid="stFileUploader"] > div {
        border: 2px dashed var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        background-color: var(--card-background);
        transition: all 0.3s ease;
    }
    div[data-testid="stFileUploader"] > div:hover {
        border-color: var(--primary-color);
        box-shadow: var(--shadow);
    }

    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] input {
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 0.2rem rgba(47, 128, 237, 0.25); /* Primary color with transparency */
    }

    /* Button Styling */
    button {
        background: linear-gradient(145deg, var(--secondary-color), #218838); /* Green gradient */
        color: white !important;
        border: none;
        border-radius: var(--border-radius) !important;
        padding: 0.75rem 1.5rem;
        font-size: 1.05rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    button:hover {
        background: linear-gradient(145deg, #218838, var(--secondary-color)); /* Reverse gradient on hover */
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    button:active {
        transform: translateY(0);
        box-shadow: none;
    }

    /* Specific button overrides */
    div[data-testid="stHorizontalBlock"] button {
        width: 100%; /* Make action buttons fill their column */
    }

    /* Success, Info, Warning, Error messages */
    .stAlert {
        border-radius: var(--border-radius);
        padding: 1rem 1.5rem;
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .stAlert.success {
        background-color: #D4EDDA !important; /* Light green */
        color: #155724 !important; /* Darker green */
        border-left: 5px solid #28A745 !important; /* Green border */
    }
    .stAlert.info {
        background-color: #D1ECF1 !important; /* Light blue */
        color: #0C5460 !important; /* Darker blue */
        border-left: 5px solid #17A2B8 !important; /* Blue border */
    }
    .stAlert.warning {
        background-color: #FFF3CD !important; /* Light amber */
        color: #856404 !important; /* Darker amber */
        border-left: 5px solid #FFC107 !important; /* Amber border */
    }
    .stAlert.error {
        background-color: #F8D7DA !important; /* Light red */
        color: #721C24 !important; /* Darker red */
        border-left: 5px solid #DC3545 !important; /* Red border */
    }

    /* Expander styling */
    div[data-testid="stExpander"] {
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        background-color: var(--card-background);
        box-shadow: var(--shadow);
        padding: 0.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    div[data-testid="stExpander"] div[role="button"] {
        background: none; /* Override button styling for expander header */
        box-shadow: none;
        padding: 0.5rem 1rem;
        font-size: 1.1em;
        font-weight: 600;
        color: var(--primary-color);
    }
    div[data-testid="stExpander"] div[role="button"]:hover {
        background-color: #F0F2F6; /* Light hover effect */
    }

    /* Specific styling for front page to re-center elements */
    .centered-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-top: 5vh; /* Adjust as needed */
    }
    .centered-title {
        font-size: 3em;
        color: var(--primary-color);
        margin-bottom: 0.5em;
    }
    .centered-subheader {
        font-size: 1.5em;
        color: var(--light-text-color);
        margin-bottom: 1em;
    }
    .feature-list {
        list-style-type: none;
        padding: 0;
        margin: 2em auto;
        max-width: 600px;
    }
    .feature-list li {
        background-color: var(--card-background);
        margin: 0.5em 0;
        padding: 0.8em 1.2em;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        font-size: 1.1em;
        color: var(--text-color);
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .centered-title {
            font-size: 2.2em;
        }
        .centered-subheader {
            font-size: 1.2em;
        }
        .stButton button {
            font-size: 0.95rem;
            padding: 0.6rem 1.2rem;
        }
    }

    /* Dialog specific styling */
    .st-dg { /* This is the class for the experimental dialog container */
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        background-color: var(--card-background);
        padding: 1.5rem;
    }

    /* Custom style for compact messages */
    .compact-message {
        background-color: #e6f7ff; /* Light blue */
        border-left: 4px solid #2196F3; /* Blue border */
        margin: 0.5rem 0;
        padding: 0.75rem 1rem;
        border-radius: var(--border-radius);
        font-size: 0.9em;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        word-break: break-word; /* Ensure long text wraps */
    }
    .compact-message.success {
        background-color: #D4EDDA;
        border-left-color: #28A745;
    }
    .compact-message.error {
        background-color: #F8D7DA;
        border-left-color: #DC3545;
    }
    .compact-message.warning {
        background-color: #FFF3CD;
        border-left-color: #FFC107;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Initialize Session State ---
initialize_session_state()

# --- Read credentials from secrets.toml ---
SENDER_EMAIL = None
SENDER_APP_PASSWORD = None
try:
    SENDER_EMAIL = st.secrets.get("SENDER_EMAIL")
    SENDER_APP_PASSWORD = st.secrets.get("SENDER_APP_PASSWORD")
    if SENDER_EMAIL is None or SENDER_APP_PASSWORD is None:
        st.error("❌ Sender email credentials (`SENDER_EMAIL` or `SENDER_APP_PASSWORD`) are missing in your `.streamlit/secrets.toml` file.")
        st.info("Please ensure your `.streamlit/secrets.toml` file contains both `SENDER_EMAIL` and `SENDER_APP_PASSWORD` keys.")
        st.markdown("Example `.streamlit/secrets.toml` content:\n```toml\nSENDER_EMAIL = \"your.email@gmail.com\"\nSENDER_APP_PASSWORD = \"your_16_character_app_password\"\n```")
        st.stop() # Stop execution if credentials are fundamentally missing
except Exception as e:
    st.error(f"❌ Error loading sender email credentials: {e}. Please ensure your `.streamlit/secrets.toml` file is correctly set up and accessible.")
    st.info("Ensure you have a folder named `.streamlit` in your app's root directory, and inside it, a file named `secrets.toml`.")
    st.markdown("Example `.streamlit/secrets.toml` content:\n```toml\nSENDER_EMAIL = \"your.email@gmail.com\"\nSENDER_APP_PASSWORD = \"your_16_character_app_password\"\n```")
    st.stop()


# --- Data Validation Function ---
def perform_data_validation(df: pd.DataFrame):
    """
    Performs comprehensive data validation on the DataFrame, attempting type conversions
    and collecting issues.

    Returns:
        tuple: (validated_df, list_of_validation_messages)
        validation_messages: List of strings, each being an error or warning message.
    """
    validation_messages = []
    df_copy = df.copy() # Work on a copy to avoid modifying original dataframe unexpectedly

    # Define all expected columns for validation
    expected_columns_for_validation = [
        'EmployeeID', 'EmployeeName', 'TransactionID', 'Date', 'Amount', 'Type', 'Description', 'Branch'
    ] + [f"{l} Paid" for l in LOAN_TYPES] + [f"{l} Remaining" for l in LOAN_TYPES]

    # 1. Check for expected columns existence
    # Missing columns will be handled downstream in PDF generation, but we'll warn here.
    for col in expected_columns_for_validation:
        if col not in df_copy.columns:
            validation_messages.append(f"⚠️ **Missing Column:** Expected column `{col}` was not found. It will be treated as 'N/A' or 0 in reports.")
            # Add the column with NaN so subsequent checks don't fail for non-existent columns
            df_copy[col] = pd.NA

    # 2. Data Type Validation and Conversion
    numeric_cols = ['Amount'] + [f"{l} Paid" for l in LOAN_TYPES] + [f"{l} Remaining" for l in LOAN_TYPES]
    for col in numeric_cols:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
            nan_count = df_copy[col].isnull().sum()
            if nan_count > 0:
                validation_messages.append(f"⚠️ **Data Type Warning:** Column `{col}` contains {nan_count} non-numeric values. These have been converted to 0 for calculations.")
                df_copy[col] = df_copy[col].fillna(0)

    if 'Date' in df_copy.columns:
        initial_invalid_dates = df_copy['Date'].isnull().sum()
        df_copy['Date'] = pd.to_datetime(df_copy['Date'], errors='coerce')
        invalid_date_count = df_copy['Date'].isnull().sum() - initial_invalid_dates

        if invalid_date_count > 0:
            validation_messages.append(f"⚠️ **Data Type Warning:** Column `Date` contains {invalid_date_count} invalid date formats. These will appear as 'N/A' in reports.")
    else:
        validation_messages.append(f"⚠️ **Column Missing:** 'Date' column was not found. Dates will be 'N/A' in reports.")

    # 3. Check for empty critical fields
    critical_for_grouping = ['EmployeeID', 'EmployeeName', 'Branch']
    for col in critical_for_grouping:
        if col in df_copy.columns:
            empty_count = df_copy[col].isnull().sum() + (df_copy[col] == '').sum()
            if empty_count > 0:
                validation_messages.append(f"⚠️ **Missing Values:** Column `{col}` has {empty_count} empty/missing values. Reports may be affected if these are critical for grouping or identification.")
        else:
            validation_messages.append(f"❌ **Critical Column Missing:** Required column `{col}` is entirely missing. This may lead to errors or incomplete reports.")


    return df_copy, validation_messages


# --- Main Content Area ---

# --- Front Page ---
if st.session_state.page == "front":
    st.title("🏦 End-of-Day (EOD) Banking Transaction Report Generator")
    st.markdown(
        """
        #### Your reliable tool for seamless daily banking transaction reports.
        - Upload transaction **CSV or Excel** file  
        - Generate **employee-wise PDF reports**  
        - Email to **multiple branch managers**
        """
    )
    if st.button("🚀 Start Generating Report"):
        st.session_state.page = "report"
        st.rerun()

# --- Report Page ---
elif st.session_state.page == "report":
    st.header("📁 Upload Transaction File")
    uploaded_file = st.file_uploader("Upload CSV or Excel file with transaction data", type=["csv", "xlsx", "xls"], key="main_upload")

    if uploaded_file is not None:
        # If a new file is uploaded or a different file is selected
        if st.session_state.uploaded_file is None or uploaded_file.name != st.session_state.uploaded_file.name:
            # Reset only file-related states for a fresh start with the new file
            st.session_state.uploaded_file = uploaded_file
            st.session_state.pdf_data = {}
            st.session_state.manager_email_dict = {}
            st.session_state.email_saved_success = False
            st.session_state.confirm_send_emails = False
            st.session_state.validation_messages = []
            st.session_state.raw_df = None # Ensures raw_df is reloaded below
            st.session_state.validated_df = None
            # No st.rerun() here immediately. Let the code flow to load the df.
    elif uploaded_file is None and st.session_state.uploaded_file is not None:
        # User has cleared the uploader (e.g., clicked 'x')
        # ONLY reset file-related state, keeping the current page ('report')
        reset_file_related_state()
        st.rerun() # Rerun to reflect the cleared state and hide dependent sections


    if st.session_state.uploaded_file:
        # Load raw_df if it hasn't been loaded for the current uploaded_file yet
        if st.session_state.raw_df is None:
            st.success(f"File '{st.session_state.uploaded_file.name}' uploaded successfully! 🎉")
            try:
                if st.session_state.uploaded_file.name.endswith(".csv"):
                    st.session_state.raw_df = pd.read_csv(st.session_state.uploaded_file)
                else:
                    st.session_state.raw_df = pd.read_excel(st.session_state.uploaded_file)

                if st.session_state.raw_df.empty or st.session_state.raw_df.columns.empty:
                    st.error("❌ Uploaded file is empty or contains no recognized columns. Please upload a file with data.")
                    reset_file_related_state() # Reset file state, stay on page
                    st.stop() # Stop this run, app will rerun with cleared state

            except Exception as e:
                st.error(f"❌ Error reading file: {e}. Please ensure it is a valid CSV or Excel file with proper formatting.")
                reset_file_related_state() # Reset file state, stay on page
                st.stop() # Stop this run, app will rerun with cleared state

            st.rerun() # Rerun after successful raw_df load to display previews and data quality

        # --- Display Raw Data Preview ---
        st.markdown("---")
        st.markdown("### 📊 Raw Data Preview (from your uploaded file)")
        st.dataframe(st.session_state.raw_df.head(5)) # Display first 5 rows for raw data preview
        st.write(f"**Total rows in raw file:** {len(st.session_state.raw_df)}")

        # --- Perform Enhanced Data Validation (Directly on the loaded raw_df) ---
        st.session_state.validated_df, st.session_state.validation_messages = perform_data_validation(st.session_state.raw_df)

        st.markdown("---")
        st.markdown("### ✅ Data Quality Report")
        if st.session_state.validation_messages:
            for msg in st.session_state.validation_messages:
                if "❌" in msg:
                    st.error(msg)
                elif "⚠️" in msg:
                    st.warning(msg)
                else:
                    st.info(msg)
            if any("❌" in msg for msg in st.session_state.validation_messages):
                st.error("Please address the critical errors above for accurate report generation. Reports might be incomplete or incorrect.")
            else:
                st.success("Please review the warnings above. Reports will be generated with processed data.")
        else:
            st.success("✅ No major data quality issues found. Data looks good!")

        st.markdown("---")

        # --- Receiver Emails per Branch ---
        st.markdown("### 📧 Enter Receiver Emails Per Branch")
        st.info("Please provide one or more email addresses for each branch, separated by commas. These are the managers who will receive the reports.")

        # Use the validated_df for branch listing
        branches = sorted(st.session_state.validated_df['Branch'].unique().tolist())

        for branch in branches:
            if branch not in st.session_state.manager_email_dict:
                st.session_state.manager_email_dict[branch] = ""

        with st.form("email_form"):
            for branch in branches:
                default_email_for_branch = st.session_state.manager_email_dict.get(branch, "")
                email_input = st.text_input(
                    f"**{branch}** Branch Emails",
                    value=default_email_for_branch,
                    key=f"email_{branch}_input",
                    placeholder="manager1@example.com, manager2@example.com"
                )
                st.session_state.manager_email_dict[branch] = email_input

            submitted_emails = st.form_submit_button("💾 Save Branch Emails")
            if submitted_emails:
                st.session_state.email_saved_success = True
                all_emails_valid = True
                for branch, emails_str in st.session_state.manager_email_dict.items():
                    if emails_str:
                        try:
                            validate_emails(emails_str)
                        except ValueError as e:
                            st.error(f"❌ Invalid email format for **{branch}** branch: {e}. Please check and correct.")
                            all_emails_valid = False
                            break
                        else: # This else belongs to try, meaning validation passed
                            pass # Email is valid for this branch
                    else:
                        st.warning(f"⚠️ No email addresses provided for **{branch}** branch.")
                if all_emails_valid:
                    st.success("✅ All branch email settings saved successfully!")
                else:
                    st.error("Some email addresses are invalid or missing. Please correct them before sending emails.")

        if st.session_state.email_saved_success:
            st.success("✅ Branch email settings saved successfully! You can now generate and send reports. 🎉")

        st.markdown("---")

        # --- Action Buttons (Generate, Send, Reset) ---
        st.markdown("### ▶️ Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🧮 Generate Reports and Preview"):
                st.session_state.email_saved_success = False
                st.session_state.confirm_send_emails = False
                with st.spinner("Generating PDF reports... This may take a moment."):
                    st.session_state.pdf_data, warnings_from_pdf_gen = generate_pdf_reports(st.session_state.validated_df)

                if warnings_from_pdf_gen:
                    st.warning("⚠️ Warnings encountered during PDF generation:")
                    for warning_msg in warnings_from_pdf_gen:
                        st.write(f"- {warning_msg}")
                st.success("✅ PDF Reports generated successfully! Scroll down to preview them. 📄")

        with col2:
            if st.button("📧 Send Emails"):
                st.session_state.email_saved_success = False
                
                if SENDER_EMAIL is None or SENDER_APP_PASSWORD is None:
                    st.error("❌ Sender email credentials are not configured. Please set `SENDER_EMAIL` and `SENDER_APP_PASSWORD` in your `.streamlit/secrets.toml` file.")
                    st.info("Example `.streamlit/secrets.toml` content:\n```\nSENDER_EMAIL = \"your.email@gmail.com\"\nSENDER_APP_PASSWORD = \"your_16_character_app_password\"\n```")
                elif not st.session_state.pdf_data:
                    st.warning("⚠️ Please generate reports (click 'Generate Reports and Preview') before attempting to send emails.")
                else:
                    has_valid_recipient = False
                    for branch, emails_str in st.session_state.manager_email_dict.items():
                        if emails_str:
                            try:
                                validate_emails(emails_str)
                                has_valid_recipient = True
                                break
                            except ValueError:
                                pass
                        if not has_valid_recipient:
                            st.error("❌ No valid recipient email addresses configured for any branch. Please enter manager emails in the section above.")
                        else:
                            st.session_state.confirm_send_emails = True

                if st.session_state.confirm_send_emails:
                    st.warning("Are you sure you want to send reports to all configured managers? This action cannot be undone.")
                    col_confirm_yes, col_confirm_no = st.columns(2)
                    with col_confirm_yes:
                        if st.button("✅ Confirm Send Reports"):
                            st.session_state.confirm_send_emails = False
                            all_sent = True
                            email_status_messages = []
                            with st.spinner("Sending emails... This might take a while for many reports. Please wait."):
                                for content in st.session_state.pdf_data.values():
                                    try:
                                        receivers_str = st.session_state.manager_email_dict.get(content['branch'], "")
                                        recipient_emails = validate_emails(receivers_str)

                                        if not recipient_emails:
                                            email_status_messages.append(f"warning: ⚠️ No valid email address(es) configured for branch: **{content['branch']}**. Skipping report for **{content['name']}**.")
                                            all_sent = False
                                            continue

                                        send_email_report(content, datetime.today().strftime("%Y-%m-%d"),
                                                          SENDER_EMAIL,
                                                          SENDER_APP_PASSWORD,
                                                          recipient_emails)
                                        email_status_messages.append(f"success: 📧 Email sent successfully for **{content['name']}** (Branch: **{content['branch']}**) to: {', '.join(recipient_emails)}.")
                                    except ValueError as ve:
                                        email_status_messages.append(f"error: ❌ Email configuration error for **{content['branch']}** branch: {ve}. Skipping report for **{content['name']}**.")
                                        all_sent = False
                                    except Exception as e:
                                        email_status_messages.append(f"error: ❌ Failed to send email for **{content['name']}** (Branch: **{content['branch']}**): {e}")
                                        all_sent = False
                            
                            st.markdown("---")
                            st.markdown("### 📧 Email Sending Results:")
                            
                            num_messages = len(email_status_messages)
                            if num_messages > 0:
                                cols_per_row = min(num_messages, 3) 
                                if cols_per_row == 0: cols_per_row = 1
                                
                                message_placeholders = st.columns(cols_per_row)
                                
                                for i, msg in enumerate(email_status_messages):
                                    msg_type = msg.split(':')[0]
                                    msg_content = msg.split(':', 1)[1].strip()
                                    with message_placeholders[i % cols_per_row]:
                                        st.markdown(f'<div class="compact-message {msg_type}">{msg_content}</div>', unsafe_allow_html=True)
                            
                            st.markdown("---")

                            if all_sent and num_messages > 0:
                                st.balloons()
                                st.success("All reports sent successfully! 🚀")
                            elif num_messages > 0:
                                st.info("Some emails failed to send. Please review the messages above.")
                            else:
                                st.info("No emails were sent (no reports generated or no valid recipients).")

                with col_confirm_no:
                    if st.button("❌ Cancel Send Reports"):
                        st.session_state.confirm_send_emails = False

        with col3:
            if st.button("🔁 Reset Application"):
                st.info("Resetting application state...")
                reset_application_state()
                st.rerun()

        # --- Display Generated PDF Reports ---
        if st.session_state.pdf_data:
            st.markdown("---")
            st.markdown("### 📄 Generated PDF Report Previews:")
            st.info("Click on an employee's report below to expand and view/download the PDF.")
            for emp_id, content in st.session_state.pdf_data.items():
                with st.expander(f"{content['name']} (Employee ID: {emp_id}) - Branch: {content['branch']}"):
                    display_pdf(content['pdf_bytes'], content['filename'])
    else:
        # This message is shown when on the 'report' page but no file is loaded
        st.info("⬆️ Please upload a CSV or Excel file above to get started.")

