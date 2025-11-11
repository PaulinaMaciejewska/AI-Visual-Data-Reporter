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
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=["png", "jpg", "jpeg"],
        help="Upload chart or graph images to analyze",
        accept_multiple_files=True
    )

    if uploaded_files:
        for uploaded_file in uploaded_files: 
                st.image(uploaded_file, caption=f"Uploaded: {uploaded_file.name}", width='stretch')
        if st.button("🔍 Analyze Charts", type="primary"):
            
            async def analyze_all_charts():
                files = []
                for uploaded_file in uploaded_files: 

                    uploaded_file.seek(0)
                    # Read image data
                    image_data = uploaded_file.read()   

                    files.append((uploaded_file.name, image_data))

                # Add user message
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Please analyze these charts: {', '.join([f[0] for f in files])}"
                })
                            
                    
                # Show analyzing message
                with st.spinner(f"Analyzing {len(uploaded_files)} chart..."):
                    try:
                        result = await st.session_state.assistant.analyze_chart(files)
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
                        
            asyncio.run(analyze_all_charts())
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