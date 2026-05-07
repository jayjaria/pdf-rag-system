import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime
from pdf_rag_system_backend import setup_pipeline_and_query

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="PDF RAG Chat",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
        color: white;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    /* Title styling */
    h1 {
        color: #1e3c72;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        margin-bottom: 20px;
        letter-spacing: -0.5px;
    }
    
    h2 {
        color: #2a5298;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 16px;
        margin-bottom: 12px;
        border-radius: 12px;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20px;
        border-radius: 18px;
        padding: 14px 18px;
        font-size: 15px;
        line-height: 1.5;
    }
    
    .bot-message {
        background: white;
        color: #333;
        margin-right: 20px;
        border-radius: 18px;
        padding: 14px 18px;
        border-left: 4px solid #667eea;
        font-size: 15px;
        line-height: 1.6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* PDF List styling */
    .pdf-item {
        background: white;
        padding: 12px;
        margin: 10px 0;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        color: #333;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    .pdf-item:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    
    .pdf-item.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-left-color: #fff;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px !important;
        border: 2px solid #e0e0e0 !important;
        font-size: 15px !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Empty state styling */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        text-align: center;
        color: #999;
    }
    
    .empty-state-icon {
        font-size: 64px;
        margin-bottom: 20px;
        opacity: 0.5;
    }
    
    .empty-state-text {
        font-size: 18px;
        color: #666;
        margin-bottom: 10px;
    }
    
    /* Loading animation */
    .loading {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #667eea;
        border-radius: 50%;
        animation: pulse 1.4s infinite;
        margin: 0 4px;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 1; }
    }
    
    /* Sidebar title */
    .sidebar-title {
        color: white;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Info box */
    .info-box {
        background: rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        padding: 12px;
        border-radius: 6px;
        font-size: 13px;
        color: #555;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== Session State Management ====================
def initialize_session():
    """Initialize session state variables"""
    if "pdf_history" not in st.session_state:
        st.session_state.pdf_history = load_pdf_history()
    
    if "current_pdf" not in st.session_state:
        st.session_state.current_pdf = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    
    if "uploaded_pdfs" not in st.session_state:
        st.session_state.uploaded_pdfs = {}

def load_pdf_history():
    """Load previously uploaded PDFs from storage"""
    history_file = Path("pdf_history.json")
    if history_file.exists():
        try:
            with open(history_file, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pdf_history():
    """Save PDF history to file"""
    with open("pdf_history.json", "w") as f:
        json.dump(st.session_state.pdf_history, f, indent=2, default=str)

def get_pdf_key(filename):
    """Generate a unique key for a PDF"""
    return filename.lower().replace(" ", "_").replace(".pdf", "")

# ==================== PDF Management ====================
def handle_pdf_upload(uploaded_file):
    """Handle PDF file upload"""
    if uploaded_file is not None:
        # Save uploaded PDF
        pdf_path = Path("uploaded_pdfs")
        pdf_path.mkdir(exist_ok=True)
        
        file_path = pdf_path / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Add to history
        pdf_key = get_pdf_key(uploaded_file.name)
        st.session_state.pdf_history[pdf_key] = {
            "filename": uploaded_file.name,
            "path": str(file_path),
            "uploaded_at": datetime.now().isoformat(),
            "size": len(uploaded_file.getvalue()) / 1024  # KB
        }
        
        # Initialize chat history for this PDF
        if pdf_key not in st.session_state.chat_history:
            st.session_state.chat_history[pdf_key] = []
        
        st.session_state.current_pdf = pdf_key
        save_pdf_history()
        
        st.success(f"✅ PDF '{uploaded_file.name}' uploaded successfully!")
        return file_path
    
    return None

def select_pdf(pdf_key):
    """Select a PDF from history"""
    st.session_state.current_pdf = pdf_key
    if pdf_key not in st.session_state.chat_history:
        st.session_state.chat_history[pdf_key] = []

def delete_pdf(pdf_key):
    """Delete a PDF from history"""
    if pdf_key in st.session_state.pdf_history:
        pdf_info = st.session_state.pdf_history[pdf_key]
        pdf_path = Path(pdf_info["path"])
        
        # Delete file if exists
        if pdf_path.exists():
            pdf_path.unlink()
        
        # Remove from history and chat
        del st.session_state.pdf_history[pdf_key]
        if pdf_key in st.session_state.chat_history:
            del st.session_state.chat_history[pdf_key]
        
        # Reset current PDF if it was selected
        if st.session_state.current_pdf == pdf_key:
            st.session_state.current_pdf = None
        
        save_pdf_history()
        st.rerun()

# ==================== Main App ====================
def main():
    initialize_session()
    
    # ============= SIDEBAR =============
    with st.sidebar:
        st.markdown('<div class="sidebar-title">📚 PDF RAG Chat</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Upload section
        st.subheader("📤 Upload PDF")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            handle_pdf_upload(uploaded_file)
        
        st.divider()
        
        # PDF History section
        st.subheader("📋 Your PDFs")
        
        if st.session_state.pdf_history:
            for pdf_key, pdf_info in st.session_state.pdf_history.items():
                col1, col2, col3 = st.columns([3, 0.5, 0.5])
                
                with col1:
                    is_active = pdf_key == st.session_state.current_pdf
                    button_style = "✓ " if is_active else ""
                    
                    if st.button(
                        f"{button_style}{pdf_info['filename']}",
                        key=f"pdf_{pdf_key}",
                        use_container_width=True
                    ):
                        select_pdf(pdf_key)
                
                with col2:
                    if st.button("🗑", key=f"del_{pdf_key}", help="Delete"):
                        delete_pdf(pdf_key)
                
                with col3:
                    num_msgs = len(st.session_state.chat_history.get(pdf_key, []))
                    st.caption(f"{num_msgs} 💬")
        else:
            st.info("📭 No PDFs uploaded yet. Upload one to get started!")
        
        st.divider()
        
        # Current PDF info
        if st.session_state.current_pdf:
            pdf_info = st.session_state.pdf_history[st.session_state.current_pdf]
            with st.expander("📊 PDF Info"):
                st.write(f"**File:** {pdf_info['filename']}")
                st.write(f"**Size:** {pdf_info['size']:.1f} KB")
                st.write(f"**Uploaded:** {pdf_info['uploaded_at'][:10]}")
    
    # ============= MAIN AREA =============
    if st.session_state.current_pdf:
        pdf_key = st.session_state.current_pdf
        pdf_info = st.session_state.pdf_history[pdf_key]
        pdf_path = pdf_info["path"]
        
        # Header
        st.markdown(f"# 💬 Chat with {pdf_info['filename']}")
        st.caption(f"Ask questions about this document. The AI will answer based on its content.")
        
        st.divider()
        
        # Chat area
        chat_container = st.container()
        
        with chat_container:
            # Display chat history
            for message in st.session_state.chat_history[pdf_key]:
                if message["role"] == "user":
                    st.markdown(
                        f'<div class="chat-message user-message">{message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="chat-message bot-message">{message["content"]}</div>',
                        unsafe_allow_html=True
                    )
        
        st.divider()
        
        # Input area
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_area(
                "Your question:",
                placeholder="Ask me anything about this PDF...",
                height=80,
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button(
                "Send",
                use_container_width=True,
                type="primary"
            )
        
        # Handle message sending
        if send_button and user_input.strip():
            # Add user message to history
            st.session_state.chat_history[pdf_key].append({
                "role": "user",
                "content": user_input
            })
            
            # Show loading state
            with st.spinner("🤔 Thinking..."):
                try:
                    # Call backend RAG system
                    response = setup_pipeline_and_query(
                        pdf_path=pdf_path,
                        question=user_input,
                        chunk_size=1000,
                        chunk_overlap=150,
                        embed_model_name="text-embedding-3-small"
                    )
                    
                    # Add bot response to history
                    st.session_state.chat_history[pdf_key].append({
                        "role": "bot",
                        "content": response
                    })
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.session_state.chat_history[pdf_key].append({
                        "role": "bot",
                        "content": error_msg
                    })
                    st.error(error_msg)
            
            st.rerun()
    
    else:
        # Empty state
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-text">No PDF Selected</div>
            <p style="color: #999; font-size: 14px;">
                Upload or select a PDF from the sidebar to begin chatting
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()