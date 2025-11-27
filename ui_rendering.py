import streamlit as st
from constants import ALLOWED_FORMATS, ALLOWED_IMAGE_FORMATS, ALLOWED_PDF_FORMAT
from session_state_manager import clear_chat
import fitz  # PyMuPDF
from streamlit.runtime.uploaded_file_manager import UploadedFile
from typing import List, Optional

def render_preview(uploaded_file: UploadedFile) -> None:
    """Render preview for uploaded file - image or PDF

    Args:
        uploaded_file: file uploaded by user
    Returns: None
    """
    file_name = uploaded_file.name.lower()

    # Image preview
    if file_name.endswith(tuple(ALLOWED_IMAGE_FORMATS)):
        st.image(uploaded_file, caption=f"Uploaded: {uploaded_file.name}", use_container_width=True)

    # PDF preview
    elif file_name.endswith(tuple(ALLOWED_PDF_FORMAT)):
        pdf_bytes = uploaded_file.read()
        first_page = fitz.open(stream=pdf_bytes, filetype="pdf")[0]
        st.image(first_page.get_pixmap().tobytes("png"), caption=f"Uploaded: {uploaded_file.name}", use_container_width=True)
        st.write(f"📄 Uploaded: {uploaded_file.name}")
        st.download_button(
            label="Download PDF",
            data=uploaded_file,
            file_name=uploaded_file.name,
            mime="application/pdf"
        )
        
        
def create_file_uploader() -> Optional[List[UploadedFile]]: 
    """Create a file uploader widget for chart images and PDF reports and return the uploaded files.

    Returns:
        Optional[List[UploadedFile]]: list of uploaded files or None if no files uploaded
    """
    st.header("📤 Upload Chart")
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=ALLOWED_FORMATS,
        help="Upload chart or graph images (PNG, JPG, JPEG) or PDF reports to analyze",
        accept_multiple_files=True
    )
    return uploaded_files

def create_clear_chat_button() -> None:
    """Create button to clear chat
    
    Returns: None
    """
    if len(st.session_state.messages) > 0:
        if st.button("🗑️ Clear Chat"):
            st.session_state.show_confirm_clear = True

    # Confirmation of deletion of chat history
    if st.session_state.get("show_confirm_clear", False):
        st.info("Are you sure you want to clear the chat? This cannot be undone.")
        col1, col2 = st.columns(2, gap="medium")
        
        action = False
        
        with col1:
            if st.button("Yes", use_container_width=True):
                clear_chat()
                st.session_state.show_confirm_clear = False
                action = True
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_confirm_clear = False
                action = True

        if action:  
            st.rerun()

def write_messages() -> None:
    """Write the messages from session state to the Streamlit chat interface.

    Returns: None
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
def manage_chat(input_message: str) -> None:
    """Manage chat input and generate assistant response.
    Args:
        input_message (str): User input message
    Returns: None
    """
    st.session_state.messages.append({"role": "user", "content": input_message})
    
    with st.chat_message("user"):
        st.write(input_message)
    
    if "last_analysis" in st.session_state:
        with st.spinner("Generating response..."):
            response = st.session_state.assistant.followup_response(input_message, st.session_state.last_analysis)
    
    else:
        response = f"I understand you're asking: '{input_message}'. Please upload a chart to analyze, or I can help with follow-up questions about the previous analysis."
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    with st.chat_message("assistant"):
        st.write(response)