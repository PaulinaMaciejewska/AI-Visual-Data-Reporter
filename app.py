import streamlit as st
import asyncio
from chart_assistant import ChartsAssistant
from ui_rendering import create_file_uploader, create_clear_chat_button, write_messages, manage_chat, render_preview
from session_state_manager import init_session_state
from files_processing import read_uploaded_files

st.title("📊 Chart Analysis Assistant")

init_session_state(ChartsAssistant)

# File uploader in sidebar
with st.sidebar:

    uploaded_files = create_file_uploader()
    create_clear_chat_button()

                          
    if uploaded_files:
        for uploaded_file in uploaded_files:
            render_preview(uploaded_file)


        if st.button("🔍 Analyze Charts", type="primary"):
            
            async def analyze_all_charts() -> None:

                converted_files = read_uploaded_files(uploaded_files)

                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Please analyze these charts: {', '.join([f[0] for f in converted_files])}"
                })
                            
                    
                # Show analyzing message
                with st.spinner(f"Analyzing {len(uploaded_files)} chart..."):
                    try:
                        result = await st.session_state.assistant.analyze_chart(converted_files)
                        st.session_state.last_analysis = result
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result
                        })
                        
                    except Exception as e:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"❌ Error analyzing chart"
                        })
                        
            asyncio.run(analyze_all_charts())
            if "last_analysis" in st.session_state:
                st.rerun()

write_messages()

input_message = st.chat_input("Ask me about the chart...")
if input_message:
    manage_chat(input_message)