# session_state_manager.py
import streamlit as st

def initialize_session_state():
    """Initializes all necessary Streamlit session state variables."""
    # Define all keys that should be in session state and their default types/values
    session_state_keys = {
        'page': "front",
        'uploaded_file': None,
        'raw_df': None, # Store the original dataframe after upload
        'validated_df': None, # Store the dataframe after validation
        'column_mapping': {}, # Stores user's selected column mapping
        'mapping_confirmed': False, # Flag to indicate if mapping step is done
        'pdf_data': {}, # Stores generated PDF bytes and metadata
        'manager_email_dict': {}, # Stores manager emails per branch
        'email_saved_success': False, # Flag for showing email save success message
        'confirm_send_emails': False, # Flag for showing email send confirmation
        'validation_messages': [] # Stores data quality report messages
    }

    for key, default_value in session_state_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def reset_application_state():
    """Resets the entire application state to its initial default values,
    including navigating back to the front page."""
    # Reset all session state variables to their initial defaults
    st.session_state.uploaded_file = None
    st.session_state.raw_df = None
    st.session_state.validated_df = None
    st.session_state.column_mapping = {}
    st.session_state.mapping_confirmed = False
    st.session_state.pdf_data = {}
    st.session_state.manager_email_dict = {}
    st.session_state.email_saved_success = False
    st.session_state.confirm_send_emails = False
    st.session_state.validation_messages = []
    st.session_state.page = "front" # Navigate back to front page

def reset_file_related_state():
    """Resets only the session state variables related to file upload and processing,
    keeping the current page state."""
    st.session_state.uploaded_file = None
    st.session_state.raw_df = None
    st.session_state.validated_df = None
    st.session_state.column_mapping = {}
    st.session_state.mapping_confirmed = False
    st.session_state.pdf_data = {}
    st.session_state.manager_email_dict = {} # Keep manager emails if desired, or clear
    st.session_state.email_saved_success = False
    st.session_state.confirm_send_emails = False
    st.session_state.validation_messages = []
    # IMPORTANT: DO NOT reset st.session_state.page here
