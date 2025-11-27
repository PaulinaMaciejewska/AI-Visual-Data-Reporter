import streamlit as st

def init_session_state(assistant_class) -> None:
    """Initialize the session state with the assistant and messages.

    Args:
        assistant_class (Class): Class of the assistant to initialize in session state
    Returns: None
    """
    if "assistant" not in st.session_state:
        st.session_state.assistant = assistant_class()
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I'm your Chart Analysis Assistant. Upload a chart image and I'll analyze it for you."
        })

def clear_chat() -> None:
    """Clear the chat history in session state.

    Returns: None
    """
    st.session_state.messages = []
    st.session_state.last_analysis = None


