import streamlit as st
import asyncio
from chart_assistant import ChartsAssistant

st.title("📊 Chart Analysis Assistant")

# Initialize assistant in session state
if "assistant" not in st.session_state:
    st.session_state.assistant = ChartsAssistant()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hello! I'm your Chart Analysis Assistant. Upload a chart image and I'll analyze it for you."
    })

# File uploader in sidebar
with st.sidebar:
    st.header("📤 Upload Chart")
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=["png", "jpg", "jpeg"],
        help="Upload a chart or graph image to analyze"
    )

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Chart", use_container_width=True)
        
        if st.button("🔍 Analyze Chart", type="primary"):
            uploaded_file.seek(0)
            # Read image data
            image_data = uploaded_file.read()
            st.image(image_data, caption="Uploaded Chart", width='stretch')
            
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": f"Please analyze this chart: {uploaded_file.name}"
            })
            
            # Show analyzing message
            with st.spinner("Analyzing chart..."):
                try:
                    result = st.session_state.assistant.analyze_chart(image_data)
                    st.session_state.last_analysis = result
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result
                    })
                    
                except Exception as e:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ Error analyzing chart: {str(e)}"
                    })
            
            st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

input_message = st.chat_input("Ask me about the chart...")
if input_message:
    st.session_state.messages.append({"role": "user", "content": input_message})
    
    with st.chat_message("user"):
        st.write(input_message)
    
    if "last_analysis" in st.session_state:
        with st.spinner("Generating response..."):
            response =st.session_state.assistant.followup_response(input_message, st.session_state.last_analysis)
    
    else:
        response = f"I understand you're asking: '{input_message}'. Please upload a chart to analyze, or I can help with follow-up questions about the previous analysis."
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    with st.chat_message("assistant"):
        st.write(response)
    
    st.rerun()