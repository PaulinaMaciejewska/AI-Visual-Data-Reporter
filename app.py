import streamlit as st
import asyncio
from chart_assistant import ChartsAssistant
import fitz # PyMuPDF

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
        type=["png", "jpg", "jpeg", "pdf"],
        help="Upload chart or graph images (PNG, JPG, JPEG) or PDF reports to analyze",
        accept_multiple_files=True
    )

    # Button to clear the chat
    if len(st.session_state.messages) > 0:
        if st.button("🗑️ Clear Chat"):
            st.session_state.show_confirm_clear = True

    # Confirmation of deletion of chat history
    if st.session_state.get("show_confirm_clear", False):
        st.info("Are you sure you want to clear the chat? This cannot be undone.")
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            if st.button("Yes", use_container_width=True):
                st.session_state.messages = []
                st.session_state.last_analysis = None
                st.session_state.show_confirm_clear = False
                st.rerun()
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_confirm_clear = False
                st.rerun()
                
    if uploaded_files:
        pdf_warning_shown = False
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name.lower()

            # Image preview
            if file_name.endswith((".png", ".jpg", ".jpeg")):
                st.image(uploaded_file, caption=f"Uploaded: {uploaded_file.name}", use_container_width=True)

            # PDF preview
            elif file_name.endswith(".pdf"):
                # PDF preview message once for pdf list
                if not pdf_warning_shown:
                    st.info("PDF preview not supported directly — it will be analyzed after clicking 'Analyze Charts'.")
                    pdf_warning_shown = True

                st.write(f"📄 Uploaded: {uploaded_file.name}")
                st.download_button(
                    label="Download PDF",
                    data=uploaded_file,
                    file_name=uploaded_file.name,
                    mime="application/pdf"
                )


        if st.button("🔍 Analyze Charts", type="primary"):
            
            async def analyze_all_charts():
                files = []
                for uploaded_file in uploaded_files: 

                    uploaded_file.seek(0)
                    # Read image data
                    image_data = uploaded_file.read()   

                    files.append((uploaded_file.name, image_data))

                # Convert PDF pages to images if needed
                converted_files = []

                for filename, file_bytes in files:
                    ext = filename.lower().split(".")[-1]

                    if ext == "pdf":
                        doc = fitz.open(stream=file_bytes, filetype="pdf")
                        for page_num, page in enumerate(doc):
                            pix = page.get_pixmap()
                            img_bytes = pix.tobytes("jpg")
                            converted_files.append((f"{filename[:-4]}_page_{page_num+1}.jpg", img_bytes))
                    else:
                        converted_files.append((filename, file_bytes))


                # Add user message
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