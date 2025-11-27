import streamlit as st
import time

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

# def init_session_state(assistant_class, timeout=30) -> None:
#     """
#     Initialize the session state with assistant and messages, 
#     with automatic soft-cleanup after inactivity.

#     Args:
#         assistant_class (Class): Class of the assistant to initialize
#         timeout (int): inactivity timeout in seconds (default: 20 minutes)
#     """
#     now = time.time()

#     # If first initialization
#     if "assistant" not in st.session_state:
#         st.session_state.assistant = assistant_class()
#         st.session_state.messages = [{
#             "role": "assistant",
#             "content": "Hello! I'm your Chart Analysis Assistant. Upload a chart image and I'll analyze it for you."
#         }]
#         st.session_state.last_use = now
#         return

#     # If last_use doesn't exist (backward compatibility)
#     if "last_use" not in st.session_state:
#         st.session_state.last_use = now

#     # Soft cleanup after inactivity
#     if now - st.session_state.last_use > timeout:
#         st.session_state.assistant = assistant_class()
#         st.session_state.messages = [{
#             "role": "assistant",
#             "content": "Hello! I'm your Chart Analysis Assistant. Upload a chart image and I'll analyze it for you."
#         }]
#         print("✔ Assistant reset due to timeout.")
#         print("✔ Messages reset.")

#     # Update last use timestamp
#     st.session_state.last_use = now

def clear_chat() -> None:
    """Clear the chat history in session state.

    Returns: None
    """
    st.session_state.messages = []
    st.session_state.last_analysis = None


