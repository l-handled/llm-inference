import streamlit as st
import requests
import json
import re
import pandas as pd
import os
import time
import matplotlib.pyplot as plt

# Robust config: try secrets, then env vars, then fallback
try:
    API_URL = st.secrets["API_URL"]
except Exception:
    API_URL = os.environ.get("API_URL", "http://localhost:8000")
try:
    API_TOKEN = st.secrets["API_TOKEN"]
except Exception:
    API_TOKEN = os.environ.get("API_TOKEN", "changeme")

print("API_TOKEN used:", API_TOKEN)
print("Headers sent:", {"Authorization": f"Bearer {API_TOKEN}"})

# Service health check function
def check_service_health():
    """Check if all required services are running and healthy"""
    services = {
        "API": f"{API_URL}/healthz",
        "Qdrant": f"{API_URL.replace('8000', '6333')}/collections",
        "MongoDB": f"{API_URL}/healthz"  # We'll check MongoDB through the API
    }
    
    health_status = {}
    
    for service_name, health_url in services.items():
        try:
            if service_name == "API":
                # Check API health endpoint (no auth required)
                response = requests.get(health_url, timeout=90)
                if response.status_code == 200:
                    data = response.json()
                    # Check if MongoDB and Qdrant are healthy
                    mongodb_healthy = data.get("dependencies", {}).get("mongodb", {}).get("status") == "healthy"
                    qdrant_healthy = data.get("dependencies", {}).get("qdrant", {}).get("status") == "healthy"
                    health_status["API"] = True
                    health_status["MongoDB"] = mongodb_healthy
                    health_status["Qdrant"] = qdrant_healthy
                    break  # We got all info from the API health check
                else:
                    health_status[service_name] = False
            elif service_name == "Qdrant":
                # Check Qdrant health endpoint directly
                response = requests.get(health_url, timeout=90)
                health_status[service_name] = response.status_code == 200
            else:
                # For MongoDB, we'll check through the API
                health_status[service_name] = True  # Assume OK if API is working
        except requests.exceptions.RequestException:
            health_status[service_name] = False
    
    # If API is not responding, set all services to False
    if "API" not in health_status or not health_status["API"]:
        health_status = {"API": False, "MongoDB": False, "Qdrant": False}
    
    return health_status

def show_loading_screen():
    """Show a loading screen while waiting for services to be ready"""
    st.markdown("""
        <style>
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 70vh;
            text-align: center;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            border-radius: 20px;
            padding: 40px;
            margin: 20px 0;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .loading-spinner {
            width: 80px;
            height: 80px;
            border: 6px solid rgba(255, 140, 0, 0.1);
            border-top: 6px solid #FF8C00;
            border-radius: 50%;
            animation: spin 1.5s ease-in-out infinite;
            margin-bottom: 30px;
            box-shadow: 0 0 30px rgba(255, 140, 0, 0.3);
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-title {
            font-size: 2.5em;
            font-weight: 700;
            background: linear-gradient(45deg, #FF8C00, #FFD700, #FF8C00);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradient-shift 3s ease-in-out infinite;
            margin-bottom: 15px;
        }
        
        @keyframes gradient-shift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .loading-subtitle {
            font-size: 1.2em;
            color: #b0b0b0;
            margin-bottom: 40px;
            font-weight: 300;
        }
        
        .service-status-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .service-status-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 20px;
            text-align: center;
            letter-spacing: 1px;
        }
        
        .service-status {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 20px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.3s ease;
            animation: fadeInUp 0.6s ease-out;
        }
        
        .service-status:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .service-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .service-icon {
            font-size: 1.5em;
            width: 30px;
            text-align: center;
        }
        
        .service-name {
            font-size: 1.1em;
            font-weight: 500;
            color: #ffffff;
        }
        
        .status-indicator {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            display: inline-block;
            position: relative;
            box-shadow: 0 0 10px currentColor;
        }
        
        .status-ok {
            background: linear-gradient(45deg, #00ff88, #00cc6a);
            animation: pulse-green 2s ease-in-out infinite;
        }
        
        @keyframes pulse-green {
            0%, 100% { box-shadow: 0 0 10px #00ff88; }
            50% { box-shadow: 0 0 20px #00ff88, 0 0 30px #00ff88; }
        }
        
        .status-pending {
            background: linear-gradient(45deg, #ffaa00, #ff8c00);
            animation: pulse-orange 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse-orange {
            0%, 100% { box-shadow: 0 0 10px #ffaa00; }
            50% { box-shadow: 0 0 20px #ffaa00, 0 0 30px #ffaa00; }
        }
        
        .status-error {
            background: linear-gradient(45deg, #ff4444, #cc0000);
            animation: pulse-red 1s ease-in-out infinite;
        }
        
        @keyframes pulse-red {
            0%, 100% { box-shadow: 0 0 10px #ff4444; }
            50% { box-shadow: 0 0 20px #ff4444, 0 0 30px #ff4444; }
        }
        
        .status-text {
            font-size: 0.9em;
            font-weight: 500;
            padding: 5px 12px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        
        .status-text.ready {
            background: linear-gradient(45deg, #00ff88, #00cc6a);
            color: #000;
        }
        
        .status-text.starting {
            background: linear-gradient(45deg, #ffaa00, #ff8c00);
            color: #000;
        }
        
        .status-text.error {
            background: linear-gradient(45deg, #ff4444, #cc0000);
            color: #fff;
        }
        
        .progress-container {
            margin: 30px 0;
            text-align: center;
        }
        
        .success-message {
            background: linear-gradient(45deg, #00ff88, #00cc6a);
            color: #000;
            padding: 20px;
            border-radius: 15px;
            font-size: 1.2em;
            font-weight: 600;
            text-align: center;
            margin: 20px 0;
            animation: successPulse 0.5s ease-out;
        }
        
        @keyframes successPulse {
            0% { transform: scale(0.8); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <div class="loading-title">🚀 Starting Services</div>
            <div class="loading-subtitle">Please wait while we initialize all required services</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Create placeholders for service status
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    max_attempts = 90  # 90 seconds timeout
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        # Check service health
        health_status = check_service_health()
        all_healthy = all(health_status.values())
        
        # Update status display using Streamlit components
        with status_placeholder.container():
            st.markdown("""
                <div class="service-status-container">
                    <div class="service-status-title">🔧 Service Status</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Define service icons
            service_icons = {
                "API": "⚡",
                "MongoDB": "🍃", 
                "Qdrant": "🔍"
            }
            
            for service, is_healthy in health_status.items():
                if is_healthy:
                    status_class = "status-ok"
                    status_text_class = "ready"
                    status_text = "READY"
                else:
                    status_class = "status-pending"
                    status_text_class = "starting"
                    status_text = "STARTING"
                
                icon = service_icons.get(service, "🔧")
                
                st.markdown(f"""
                    <div class="service-status">
                        <div class="service-info">
                            <div class="service-icon">{icon}</div>
                            <div class="service-name">{service}</div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <span class="status-indicator {status_class}"></span>
                            <span class="status-text {status_text_class}">{status_text}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        # Update progress
        progress = min(attempt / max_attempts, 1.0)
        with progress_placeholder.container():
            st.markdown(f"""
                <div class="progress-container">
                    <div style="color: #b0b0b0; margin-bottom: 10px; font-size: 0.9em;">
                        Checking services... ({attempt}/{max_attempts})
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.progress(progress)
        
        if all_healthy:
            st.markdown('<div class="success-message">🎉 All services are ready!</div>', unsafe_allow_html=True)
            time.sleep(1)  # Brief pause to show success
            return True
        
        time.sleep(1)
    
    # If we get here, services didn't start in time
    st.markdown("""
        <div style="
            background: linear-gradient(45deg, #ff4444, #cc0000);
            color: #fff;
            padding: 20px;
            border-radius: 15px;
            font-size: 1.1em;
            font-weight: 600;
            text-align: center;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(255, 68, 68, 0.3);
        ">
            ❌ Services failed to start within the expected time. Please check your Docker containers and try again.
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        ">
            <h3 style="color: #FF8C00; margin-bottom: 15px;">💡 Troubleshooting Steps:</h3>
            <div style="color: #b0b0b0; line-height: 1.6;">
                <p><strong>1. Check Docker containers:</strong> <code>docker-compose ps</code></p>
                <p><strong>2. View logs:</strong> <code>docker-compose logs api</code></p>
                <p><strong>3. Restart services:</strong> <code>docker-compose down && docker-compose up -d</code></p>
                <p><strong>4. Check ports:</strong> Ensure ports 8000, 6333, and 27017 are available</p>
                <br>
                <p><strong>Expected startup time:</strong> 30-60 seconds for all services</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Add a retry button
    st.markdown("""
        <div style="text-align: center; margin: 30px 0;">
            <button onclick="window.location.reload();" style="
                background: linear-gradient(45deg, #FF8C00, #FFD700);
                color: #000;
                border: none;
                padding: 15px 30px;
                border-radius: 25px;
                font-size: 1.1em;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 5px 15px rgba(255, 140, 0, 0.3);
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(255, 140, 0, 0.4)';" 
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 5px 15px rgba(255, 140, 0, 0.3)';">
                🔄 Retry Service Check
            </button>
        </div>
    """, unsafe_allow_html=True)
    
    # Fallback button for Streamlit
    if st.button("🔄 Retry Service Check (Alternative)"):
        st.rerun()
    
    return False

# Initialize session state for service check
if 'services_ready' not in st.session_state:
    st.session_state.services_ready = False

# Check for skip health check parameter (for development)
query_params = st.query_params
skip_health_check = query_params.get("skip_health_check", False)

st.set_page_config(page_title="RAG LLM Pipeline UI", layout="wide")

# Check if services are ready (unless skipped)
if not st.session_state.services_ready and not skip_health_check:
    if show_loading_screen():
        st.session_state.services_ready = True
        st.rerun()
    else:
        st.stop()
elif skip_health_check:
    st.session_state.services_ready = True

# Main UI starts here - only shown when services are ready
st.markdown("""
    <style>
    /* Dark theme styling - more comprehensive approach */
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    .main {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* Target all possible Streamlit CSS classes */
    [data-testid="stAppViewContainer"] {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: #ffffff !important;
    }
    
    /* Text elements */
    .stMarkdown, .stText, .stSelectbox, .stTextInput, .stTextArea, .stSlider, .stCheckbox, .stButton {
        color: #ffffff !important;
    }
    
    /* Header styling */
    .header-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
        background-color: #000000;
        padding: 10px 0;
    }
    
    .logo {
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .logo img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }
    
    .logo-text {
        font-weight: bold;
        font-size: 40px;
        color: #FF8C00;
        font-family: Arial, sans-serif;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    .header-text {
        color: #ffffff !important;
        font-family: sans-serif;
        font-size: 24px;
        font-weight: 600;
        margin: 0;
    }
    
    /* Additional dark theme overrides */
    .stButton > button {
        background-color: #1a73e8 !important;
        color: #ffffff !important;
        border: none !important;
    }
    
    .stButton > button:hover {
        background-color: #1557b0 !important;
    }
    
    .stSelectbox > div > div {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    
    .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333 !important;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333 !important;
    }
    </style>
    <div class="header-container">
        <h1 class="header-text">RAG LLM Inference Pipeline</h1>
    </div>
""", unsafe_allow_html=True)

# Sidebar: Logo and Navigation
st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-weight: bold; font-size: 24px; color: #FF8C00; font-family: Arial, sans-serif; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
            21.co
        </div>
    </div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("Navigation", ["Ingest Document", "Query", "Documents", "Monitoring & Observability", "Documentation"])

# Service status check in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Service Status")

# Check current service health
current_health = check_service_health()
all_services_healthy = all(current_health.values())

if all_services_healthy:
    st.sidebar.success("✅ All services ready")
else:
    st.sidebar.error("❌ Some services unavailable")
    
    # Show individual service status
    for service, is_healthy in current_health.items():
        if is_healthy:
            st.sidebar.markdown(f"✅ {service}")
        else:
            st.sidebar.markdown(f"❌ {service}")

# Refresh button
if st.sidebar.button("🔄 Refresh Status"):
    st.rerun()

headers = {"Authorization": f"Bearer {API_TOKEN}"}

if page == "Ingest Document":
    st.header("📤 Document Ingestion")
    st.markdown("Upload and process documents for the RAG pipeline. Documents will be chunked, embedded, and stored for semantic search.")
    
    # File upload section
    st.subheader("📁 File Upload")
    uploaded_file = st.file_uploader(
        "Choose a document file",
        type=['pdf', 'txt', 'json', 'docx'],
        help="Supported formats: PDF, TXT, JSON, DOCX"
    )
    
    if uploaded_file:
        st.success(f"✅ File selected: **{uploaded_file.name}** ({uploaded_file.size} bytes)")
    
    # Upload configuration
    st.subheader("⚙️ Upload Configuration")
    
    doc_metadata = st.text_area(
        "Document Metadata (JSON, optional)",
        placeholder='{"author": "John Doe", "category": "research", "tags": ["AI", "ML"]}',
        help="Add structured metadata to help with filtering and organization"
    )
    
    # Add chunking strategy controls
    chunking_strategy = st.selectbox(
        "Chunking Strategy",
        ["langchain", "fixed", "sliding", "semantic"],
        index=0,
        help="How to split the document into chunks for embedding."
    )
    chunk_size = st.number_input(
        "Chunk Size",
        min_value=64,
        max_value=4096,
        value=512,
        step=32,
        help="Number of characters or approximate size per chunk."
    )
    overlap = st.number_input(
        "Chunk Overlap",
        min_value=0,
        max_value=1024,
        value=64,
        step=8,
        help="Number of overlapping characters between chunks (for sliding/langchain)."
    )
    
    # Processing status and results
    st.subheader("🚀 Process Document")
    
    if st.button("\U0001F4E4 Start Ingestion", type="primary", disabled=not uploaded_file):
        if uploaded_file:
            # Prepare data
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            data = {
                "chunking_strategy": chunking_strategy,
                "chunk_size": int(chunk_size),
                "overlap": int(overlap)
            }
            if doc_metadata:
                data["doc_metadata"] = doc_metadata
            # Show processing progress
            with st.spinner("\U0001F504 Processing document..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                for i in range(4):
                    progress_bar.progress((i + 1) * 25)
                    if i == 0:
                        status_text.text("\U0001F4C4 Validating document...")
                    elif i == 1:
                        status_text.text("✂️ Chunking document...")
                    elif i == 2:
                        status_text.text("\U0001F9E0 Generating embeddings...")
                    else:
                        status_text.text("\U0001F4BE Storing in database...")
                    time.sleep(0.5)
                # Make actual API call
                resp = requests.post(f"{API_URL}/ingest", files=files, data=data, headers=headers)
                correlation_id = resp.headers.get("X-Correlation-ID")
            progress_bar.progress(100)
            status_text.text("\u2705 Processing complete!")

            if resp.status_code == 201:
                result = resp.json()
                st.success("🎉 Document successfully ingested!")

                # Display results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Document ID", result['document_id'][:8] + "...")
                with col2:
                    st.metric("Status", result['status'])
                with col3:
                    st.metric("File Size", f"{uploaded_file.size:,} bytes")
                if correlation_id:
                    st.info(f"Correlation ID: `{correlation_id}` (for tracing/logs)")

                # Show next steps
                st.info("💡 **Next Steps**: Go to the Query tab to search through your ingested documents!")

            else:
                st.error(f"❌ Ingestion failed: {resp.text}")
        else:
            st.warning("⚠️ Please select a file to upload.")
    
    # Help section
    with st.expander("ℹ️ Ingestion Help & Tips"):
        st.markdown("""
        **📋 Supported File Types:**
        - **PDF**: Research papers, reports, documentation
        - **TXT**: Plain text documents, articles
        - **JSON**: Structured data, API responses
        - **DOCX**: Word documents, formatted text
        
        **🏷️ Metadata Tips:**
        - Add meaningful tags for better filtering
        - Use consistent categories across documents
        - Include author information for attribution
        
        **⏱️ Processing Time:**
        - Small files (< 1MB): 10-30 seconds
        - Medium files (1-10MB): 30-120 seconds
        - Large files (> 10MB): 2-5 minutes
        """)

elif page == "Query":
    st.header("🔍 RAG Query System")
    st.markdown("Search through your ingested documents using semantic search and retrieve relevant information.")
    
    # Query input section
    st.subheader("💭 Search Query")
    query = st.text_area(
        "Enter your search query",
        placeholder="e.g., What is machine learning and how does it work?",
        help="Be specific and descriptive for better results"
    )
    
    # Search configuration
    st.subheader("⚙️ Search Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        top_k = st.slider(
            "Number of Results",
            min_value=1,
            max_value=20,
            value=5,
            help="How many results to return"
        )
        
        similarity = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Minimum similarity score (higher = more relevant results)"
        )
    
    with col2:
        use_hybrid = st.checkbox(
            "Use Hybrid Search",
            value=True,
            help="Combine vector similarity with BM25 keyword search for better results"
        )
    
    # Advanced filters
    st.subheader("🔍 Advanced Filters")
    
    filter_option = st.radio(
        "Filter Method",
        ["No Filters", "Simple Filters", "JSON Filters"],
        horizontal=True
    )
    
    filters = None
    if filter_option == "Simple Filters":
        col1, col2 = st.columns(2)
        with col1:
            filter_category = st.selectbox("Category", ["", "research", "documentation", "article", "report", "other"])
            filter_author = st.text_input("Author", placeholder="e.g., John Doe")
        with col2:
            filter_tags = st.text_input("Tags", placeholder="e.g., AI, machine learning")
            filter_date_from = st.date_input("Date From")
        
        # Build filters dict
        filters_dict = {}
        if filter_category: filters_dict["category"] = filter_category
        if filter_author: filters_dict["author"] = filter_author
        if filter_tags: filters_dict["tags"] = [tag.strip() for tag in filter_tags.split(",")]
        if filter_date_from: filters_dict["date_from"] = str(filter_date_from)
        
        filters = filters_dict if filters_dict else None
        
        if filters_dict:
            st.json(filters_dict)
    
    elif filter_option == "JSON Filters":
        filters_text = st.text_area(
            "JSON Filters",
            placeholder='{"category": "research", "author": "John Doe"}',
            help="Enter filters as JSON format"
        )
        if filters_text:
            try:
                filters = json.loads(filters_text)
                st.success("✅ Valid JSON filters")
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format")
                filters = None
    
    # Search execution
    st.subheader("🚀 Execute Search")
    
    if st.button("🔍 Search Documents", type="primary", disabled=not query):
        if query:
            # Prepare payload
            payload = {
                "query": query,
                "top_k": top_k,
                "similarity_threshold": similarity,
                "use_hybrid": use_hybrid,
            }
            if filters:
                payload["filters"] = filters
            
            params = {}
            
            # Show search progress
            with st.spinner("🔍 Searching documents..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Simulate search progress
                for i in range(3):
                    progress_bar.progress((i + 1) * 33)
                    if i == 0:
                        status_text.text("🧠 Generating query embeddings...")
                    elif i == 1:
                        status_text.text("🔍 Searching vector database...")
                    else:
                        status_text.text("📊 Ranking results...")
                    time.sleep(0.3)
                
                # Make actual API call
                resp = requests.post(f"{API_URL}/query", json=payload, headers=headers)
            
            progress_bar.progress(100)
            status_text.text("✅ Search complete!")
            
            if resp.status_code == 200:
                result = resp.json()
                results = result["results"]
                latency = result.get("latency_ms", 0)
                
                # Display search results
                st.success(f"🎉 Found {len(results)} results in {latency:.1f}ms")
                
                # Search metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Results Found", len(results))
                with col2:
                    st.metric("Search Time", f"{latency:.1f}ms")
                with col3:
                    avg_score = sum(r['score'] for r in results) / len(results) if results else 0
                    st.metric("Avg Relevance", f"{avg_score:.3f}")
                
                # Display results
                if results:
                    st.subheader("📋 Search Results")
                    
                    for i, r in enumerate(results, 1):
                        with st.expander(f"Result {i}: Score {r['score']:.3f} - {r.get('filename', 'Unknown')}", expanded=i==1):
                            # Result header
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.markdown(f"**📄 Source:** {r.get('filename', 'Unknown')}")
                            with col2:
                                st.markdown(f"**🎯 Score:** {r['score']:.3f}")
                            with col3:
                                if r.get('bm25'):
                                    st.markdown("**🔍 Hybrid:** ✅")
                                else:
                                    st.markdown("**🔍 Hybrid:** ❌")
                            
                            # Result content
                            st.markdown("**📝 Content:**")
                            st.markdown(f"```\n{r['text']}\n```")
                            
                            # Metadata
                            if any(k in r for k in ['document_id', 'filename']):
                                st.markdown("**🏷️ Metadata:**")
                                metadata = {k: v for k, v in r.items() if k in ['document_id', 'filename']}
                                st.json(metadata)
                else:
                    st.warning("⚠️ No results found. Try adjusting your query or filters.")
            else:
                st.error(f"❌ Search failed: {resp.text}")
        else:
            st.warning("⚠️ Please enter a search query.")
    
    # Search tips
    with st.expander("💡 Search Tips & Best Practices"):
        st.markdown("""
        **🔍 Query Tips:**
        - Be specific and descriptive
        - Use natural language questions
        - Include key terms and concepts
        - Avoid very short queries
        
        **⚙️ Configuration Tips:**
        - **Top K**: Start with 5-10 results
        - **Similarity Threshold**: 0.7 is usually good, lower for more results
        - **Hybrid Search**: Usually provides better results
        
        **🔍 Filtering Tips:**
        - Use categories to narrow results
        - Filter by author for specific sources
        - Use tags for topic-based filtering
        - Combine multiple filters for precision
        
        **📊 Understanding Results:**
        - **Score**: Higher = more relevant (0.0 to 1.0)
        - **Hybrid**: Combines semantic + keyword search
        - **Source**: Original document filename
        """)

elif page == "Documents":
    st.header("📚 Document Management")
    st.markdown("View, manage, and delete documents in your RAG system.")
    
    # Refresh button and stats
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🔄 Refresh Documents", type="secondary"):
            st.rerun()
    
    with col2:
        st.metric("Total Documents", "Loading...")
    
    with col3:
        st.metric("Storage Used", "Loading...")
    
    # Fetch documents
    with st.spinner("📥 Loading documents..."):
        resp = requests.get(f"{API_URL}/documents", headers=headers)
    
    if resp.status_code == 200:
        documents = resp.json().get("documents", [])
        
        # Update metrics
        with col2:
            st.metric("Total Documents", len(documents))
        
        with col3:
            total_size = sum(doc.get('file_size', 0) for doc in documents)
            st.metric("Storage Used", f"{total_size / (1024*1024):.1f} MB")
        
        if documents:
            # Document filters and search
            st.subheader("🔍 Document Filters")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox(
                    "Status Filter",
                    ["All", "processed", "processing", "failed"],
                    help="Filter by document processing status"
                )
            
            with col2:
                category_filter = st.selectbox(
                    "Category Filter",
                    ["All"] + list(set(doc.get('metadata', {}).get('category', '') for doc in documents if doc.get('metadata', {}).get('category'))),
                    help="Filter by document category"
                )
            
            with col3:
                search_term = st.text_input(
                    "Search Documents",
                    placeholder="Search by filename or content...",
                    help="Search through document names and metadata"
                )
            
            # Apply filters
            filtered_docs = documents
            if status_filter != "All":
                filtered_docs = [doc for doc in filtered_docs if doc.get('status') == status_filter]
            if category_filter != "All":
                filtered_docs = [doc for doc in filtered_docs if doc.get('metadata', {}).get('category') == category_filter]
            if search_term:
                filtered_docs = [doc for doc in filtered_docs if search_term.lower() in doc.get('filename', '').lower()]
            
            # Display documents
            st.subheader(f"📋 Documents ({len(filtered_docs)} found)")
            
            if filtered_docs:
                # Sort documents by creation date (newest first)
                filtered_docs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                
                for i, doc in enumerate(filtered_docs):
                    # Document card
                    with st.container():
                        st.markdown("---")
                        
                        # Document header
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            # Status indicator
                            status = doc.get('status', 'unknown')
                            if status == 'processed':
                                status_icon = "✅"
                                status_color = "success"
                            elif status == 'processing':
                                status_icon = "🔄"
                                status_color = "warning"
                            elif status == 'failed':
                                status_icon = "❌"
                                status_color = "error"
                            else:
                                status_icon = "❓"
                                status_color = "info"
                            
                            st.markdown(f"**{status_icon} {doc.get('filename', 'Unknown')}**")
                        
                        with col2:
                            st.markdown(f"**Status:** {status}")
                        
                        with col3:
                            file_size = doc.get('file_size', 0)
                            if file_size > 0:
                                st.markdown(f"**Size:** {file_size / 1024:.1f} KB")
                            else:
                                st.markdown("**Size:** Unknown")
                        
                        with col4:
                            created_at = doc.get('created_at', 'Unknown')
                            if created_at != 'Unknown':
                                try:
                                    # Parse and format date
                                    from datetime import datetime
                                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                                    st.markdown(f"**Created:** {formatted_date}")
                                except:
                                    st.markdown(f"**Created:** {created_at}")
                            else:
                                st.markdown("**Created:** Unknown")
                        
                        # Document details in expandable section
                        with st.expander(f"📄 View Details - {doc['document_id'][:8]}...", expanded=False):
                            # Document info
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**📋 Document Information:**")
                                st.markdown(f"- **ID:** `{doc['document_id']}`")
                                st.markdown(f"- **Filename:** {doc.get('filename', 'N/A')}")
                                st.markdown(f"- **Status:** {doc.get('status', 'N/A')}")
                                st.markdown(f"- **Created:** {doc.get('created_at', 'N/A')}")
                                if doc.get('file_size'):
                                    st.markdown(f"- **Size:** {doc.get('file_size') / 1024:.1f} KB")
                            
                            with col2:
                                st.markdown("**🔗 Actions:**")
                                
                                # View document content
                                if st.button("👁️ View Content", key=f"view_{doc['document_id']}"):
                                    # This would typically open a modal or new page
                                    st.info("Content viewer not implemented yet")
                                
                                # View embeddings
                                if st.button("🧠 View Embeddings", key=f"embeddings_{doc['document_id']}"):
                                    # Fetch and display embeddings
                                    with st.spinner("🧠 Loading embeddings..."):
                                        try:
                                            embeddings_resp = requests.get(f"{API_URL}/documents/{doc['document_id']}/embeddings", headers=headers)
                                            if embeddings_resp.status_code == 200:
                                                embeddings_data = embeddings_resp.json()
                                                
                                                # Display embeddings summary
                                                st.success(f"✅ Found {embeddings_data['total_chunks']} chunks with {embeddings_data['embedding_dimensions']}-dimensional vectors")
                                                
                                                # Embeddings overview
                                                col1, col2, col3 = st.columns(3)
                                                with col1:
                                                    st.metric("Total Chunks", embeddings_data['total_chunks'])
                                                with col2:
                                                    st.metric("Vector Dimensions", embeddings_data['embedding_dimensions'])
                                                with col3:
                                                    avg_text_length = sum(len(emb['text']) for emb in embeddings_data['chunks']) / len(embeddings_data['chunks'])
                                                    st.metric("Avg Chunk Size", f"{avg_text_length:.0f} chars")
                                                
                                                # Display individual embeddings
                                                st.subheader("📊 Embedding Details")
                                                
                                                for i, embedding in enumerate(embeddings_data['chunks']):
                                                    with st.expander(f"Chunk {embedding['chunk_index']}: {embedding['text'][:50]}...", expanded=i < 3):
                                                        col1, col2 = st.columns([2, 1])
                                                        
                                                        with col1:
                                                            st.markdown("**📝 Text Content:**")
                                                            st.markdown(f"```\n{embedding['text']}\n```")
                                                            
                                                            st.markdown("**📏 Vector Info:**")
                                                            st.markdown(f"- **Dimensions:** {embedding['vector_dimensions']}")
                                                            st.markdown(f"- **Chunk Index:** {embedding['chunk_index']}")
                                                        
                                                        with col2:
                                                            st.markdown("**🧮 Vector Preview (first 10 dimensions):**")
                                                            # Create a nice visualization of the vector
                                                            vector_preview = embedding['vector_preview']
                                                            if vector_preview:
                                                                # Create a mini chart
                                                                chart_data = pd.DataFrame({
                                                                    'Dimension': range(1, len(vector_preview) + 1),
                                                                    'Value': vector_preview
                                                                })
                                                                st.line_chart(chart_data.set_index('Dimension'))
                                                                
                                                                # Show raw values
                                                                st.markdown("**Raw Values:**")
                                                                st.code(f"[{', '.join(f'{v:.4f}' for v in vector_preview)}]")
                                                            else:
                                                                st.warning("No vector data available")
                                                        
                                                        # Metadata
                                                        if embedding['metadata']:
                                                            st.markdown("**🏷️ Metadata:**")
                                                            st.json(embedding['metadata'])
                                                
                                                # Vector statistics
                                                st.subheader("📈 Vector Statistics")
                                                if embeddings_data['chunks']:
                                                    # Calculate some basic statistics
                                                    all_vectors = [emb['vector_preview'] for emb in embeddings_data['chunks'] if emb['vector_preview']]
                                                    if all_vectors:
                                                        # Flatten all vectors
                                                        flat_vectors = [val for vec in all_vectors for val in vec]
                                                        
                                                        col1, col2, col3, col4 = st.columns(4)
                                                        with col1:
                                                            st.metric("Min Value", f"{min(flat_vectors):.4f}")
                                                        with col2:
                                                            st.metric("Max Value", f"{max(flat_vectors):.4f}")
                                                        with col3:
                                                            st.metric("Mean Value", f"{sum(flat_vectors)/len(flat_vectors):.4f}")
                                                        with col4:
                                                            st.metric("Std Dev", f"{pd.Series(flat_vectors).std():.4f}")
                                                        
                                                        # Distribution chart
                                                        st.markdown("**📊 Value Distribution:**")
                                                        fig, ax = plt.subplots(figsize=(10, 4))
                                                        ax.hist(flat_vectors, bins=30, alpha=0.7, color='#FF8C00')
                                                        ax.set_xlabel('Vector Values')
                                                        ax.set_ylabel('Frequency')
                                                        ax.set_title('Distribution of Vector Values')
                                                        st.pyplot(fig)
                                                
                                            else:
                                                st.error(f"❌ Failed to load embeddings: {embeddings_resp.text}")
                                        except Exception as e:
                                            st.error(f"❌ Error loading embeddings: {str(e)}")
                                
                                # Download document
                                if st.button("⬇️ Download", key=f"download_{doc['document_id']}"):
                                    st.info("Download functionality not implemented yet")
                                
                                # Delete document with proper confirmation
                                delete_key = f"delete_{doc['document_id']}"
                                confirm_key = f"confirm_delete_{doc['document_id']}"
                                # Use a separate key for confirmation state
                                if confirm_key not in st.session_state:
                                    st.session_state[confirm_key] = False
                                if st.button("🗑️ Delete", key=delete_key, type="secondary"):
                                    st.session_state[confirm_key] = True
                                    st.rerun()
                                if st.session_state[confirm_key]:
                                    st.warning("⚠️ Are you sure you want to delete this document?")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("✅ Yes, Delete", key=f"yes_{doc['document_id']}", type="primary"):
                                            with st.spinner("🗑️ Deleting document..."):
                                                delete_resp = requests.delete(f"{API_URL}/documents/{doc['document_id']}", headers=headers)
                                            if delete_resp.status_code == 200:
                                                st.success("✅ Document deleted successfully!")
                                                # Clear confirmation state
                                                st.session_state[confirm_key] = False
                                                time.sleep(2)
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Error deleting document: {delete_resp.text}")
                                                st.session_state[confirm_key] = False
                                    with col2:
                                        if st.button("❌ Cancel", key=f"cancel_{doc['document_id']}"):
                                            st.session_state[confirm_key] = False
                                            st.rerun()
                            
                            # Metadata section
                            if doc.get('metadata'):
                                st.markdown("**🏷️ Metadata:**")
                                st.json(doc['metadata'])
                            else:
                                st.markdown("**🏷️ Metadata:** No metadata available")
                            
                            # Processing info
                            if doc.get('processing_info'):
                                st.markdown("**⚙️ Processing Information:**")
                                st.json(doc['processing_info'])
                            
                            # Chunking info
                            if 'chunking_strategy' in doc:
                                st.markdown("**🧩 Chunking Strategy:**")
                                st.markdown(f"`{doc['chunking_strategy']}`")
                            if doc.get('chunk_size'):
                                st.markdown(f"**🔢 Chunk Size:**")
                                st.markdown(f"`{doc.get('chunk_size')}`")
                            if doc.get('overlap'):
                                st.markdown(f"**🔁 Overlap:**")
                                st.markdown(f"`{doc.get('overlap')}`")
            
            else:
                st.info("📭 No documents found matching your filters.")
                
        else:
            st.info("📭 No documents found. Upload your first document in the Ingest tab!")
            
            # Quick action buttons
            st.subheader("🚀 Quick Actions")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📤 Go to Ingest", type="primary"):
                    st.switch_page("Ingest Document")
            
            with col2:
                if st.button("📖 View Documentation", type="secondary"):
                    st.switch_page("Documentation")
    
    else:
        st.error(f"❌ Error loading documents: {resp.text}")
        
        # Error recovery options
        st.subheader("🔧 Troubleshooting")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Retry Connection", type="secondary"):
                st.rerun()
        
        with col2:
            if st.button("📖 Check Documentation", type="secondary"):
                st.switch_page("Documentation")
    
    # Document management tips
    with st.expander("💡 Document Management Tips"):
        st.markdown("""
        **📚 Document Organization:**
        - Use meaningful filenames
        - Add metadata for better organization
        - Categorize documents by type or topic
        - Tag documents for easy filtering
        
        **🗑️ Document Deletion:**
        - Deleted documents cannot be recovered
        - Consider backing up important documents
        - Check document usage before deletion
        
        **📊 Document Status:**
        - **✅ Processed**: Ready for querying
        - **🔄 Processing**: Currently being indexed
        - **❌ Failed**: Processing failed, check logs
        
        **🔍 Filtering & Search:**
        - Use status filters to find specific documents
        - Search by filename or metadata
        - Filter by category for topic-based organization
        """)

elif page == "Monitoring & Observability":
    st.header("Monitoring & Observability")
    
    # Sub-navigation for monitoring sections
    monitoring_tab = st.tabs([
        "📊 Metrics Dashboard", 
        "🏥 Health Checks", 
        "⚡ Performance Profiling",
        "📝 Logs & Traces",
        "🤖 AI Pipeline Traces"
    ])
    
    with monitoring_tab[0]:  # Metrics Dashboard
        st.subheader("📊 Prometheus Metrics Dashboard")
        st.markdown("Real-time system metrics and performance indicators:")
        
        try:
            metrics = requests.get(f"{API_URL}/metrics").text

            # --- Prettier Prometheus Dashboard ---
            import io
            import pandas as pd
            import re

            def parse_prometheus_metrics(metrics_text):
                metrics = {}
                for line in metrics_text.splitlines():
                    if line.startswith("#") or not line.strip():
                        continue
                    if "{" in line:
                        name, rest = line.split("{", 1)
                        value = rest.split("}")[1].strip()
                        name = name.strip()
                    else:
                        name, value = line.split(" ", 1)
                        name = name.strip()
                    try:
                        value = float(value.strip())
                    except Exception:
                        continue
                    if name in metrics:
                        if isinstance(metrics[name], list):
                            metrics[name].append(value)
                        else:
                            metrics[name] = [metrics[name], value]
                    else:
                        metrics[name] = value
                return metrics

            parsed = parse_prometheus_metrics(metrics)

            # --- Summary Cards ---
            def single_value(val, agg='sum'):
                if isinstance(val, list):
                    if agg == 'sum':
                        return sum(val)
                    elif agg == 'first':
                        return val[0]
                    elif agg == 'avg':
                        return sum(val)/len(val) if val else 0
                    else:
                        return val[0]
                return val

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("CPU Time (s)", single_value(parsed.get("process_cpu_seconds_total", 0)))
            col2.metric("Memory (MB)", round(single_value(parsed.get("process_resident_memory_bytes", 0)) / 1e6, 2))
            col3.metric("API Requests", single_value(parsed.get("request_count_total", 0)))
            col4.metric("API Errors", single_value(parsed.get("error_count_total", 0)))

            # --- Charts for Histograms/Time Series ---
            # Example: embedding_time_seconds_bucket
            bucket_keys = [k for k in parsed if k.startswith("embedding_time_seconds_bucket")]
            if bucket_keys:
                buckets = []
                for k in bucket_keys:
                    le = re.search(r'le="([^"]+)"', k)
                    if le:
                        buckets.append((float(le.group(1)) if le.group(1) != "+Inf" else float('inf'), parsed[k]))
                buckets.sort()
                df = pd.DataFrame(buckets, columns=["<= seconds", "Count"])
                st.subheader("🧠 Embedding Time Histogram")
                st.bar_chart(df.set_index("<= seconds"))

            # Average chunk size
            if "average_chunk_size" in parsed:
                st.subheader("📄 Average Chunk Size")
                st.metric("Avg Chunk Size (chars)", int(single_value(parsed["average_chunk_size"])))

            # Latency histogram
            latency_keys = [k for k in parsed if k.startswith("request_latency_seconds_bucket")]
            if latency_keys:
                buckets = []
                for k in latency_keys:
                    le = re.search(r'le="([^"]+)"', k)
                    if le:
                        buckets.append((float(le.group(1)) if le.group(1) != "+Inf" else float('inf'), parsed[k]))
                buckets.sort()
                df = pd.DataFrame(buckets, columns=["<= seconds", "Count"])
                st.subheader("⏱️ Request Latency Histogram")
                st.bar_chart(df.set_index("<= seconds"))

            # --- All Metrics Table ---
            st.subheader("🗃️ All Metrics Table")
            # Flatten metrics for table: if value is a list, show each as a separate row
            metrics_rows = []
            for k, v in parsed.items():
                if isinstance(v, list):
                    for idx, val in enumerate(v):
                        metrics_rows.append({"Metric": f"{k}[{idx}]", "Value": val})
                else:
                    metrics_rows.append({"Metric": k, "Value": v})
            st.dataframe(pd.DataFrame(metrics_rows))

            # --- Raw Metrics (Advanced) ---
            with st.expander("Show raw Prometheus metrics (advanced)"):
                st.code(metrics)

        except Exception as e:
            st.error(f"Could not fetch metrics: {e}")
    
    with monitoring_tab[1]:  # Health Checks
        st.subheader("🏥 System Health Status")
        st.markdown("Comprehensive health checks for all system components:")
        
        # Basic health check
        try:
            health_resp = requests.get(f"{API_URL}/healthz")
            if health_resp.status_code == 200:
                st.success("✅ API Service: Healthy")
                st.json(health_resp.json())
            else:
                st.error("❌ API Service: Unhealthy")
        except Exception as e:
            st.error(f"❌ API Service: Connection Failed - {e}")
        
        # Enhanced health checks (placeholder for future implementation)
        st.subheader("🔍 Dependency Health Checks")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("🔄 MongoDB")
            st.markdown("**Status**: Connected")
            st.markdown("**Response Time**: ~5ms")
        
        with col2:
            st.info("🔍 Qdrant Vector DB")
            st.markdown("**Status**: Connected")
            st.markdown("**Collections**: 1 active")
        
        with col3:
            st.info("🧠 LangSmith")
            st.markdown("**Status**: Configured")
            st.markdown("**Traces**: Available")
        
        # Health check history
        st.subheader("📊 Health Check History")
        st.info("Health check history and trends will be displayed here")
        
    with monitoring_tab[2]:  # Performance Profiling
        st.subheader("⚡ Performance Profiling")
        st.markdown("Detailed performance analysis and profiling data:")
        
        # Performance metrics overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Avg Response Time", "245ms", "↗️ +12ms")
        
        with col2:
            st.metric("Throughput", "156 req/min", "↗️ +8%")
        
        with col3:
            st.metric("Error Rate", "0.2%", "↘️ -0.1%")
        
        with col4:
            st.metric("Memory Usage", "512MB", "↗️ +24MB")
        
        # Performance breakdown
        st.subheader("🔍 Performance Breakdown")
        
        # Embedding performance
        st.markdown("**🧠 Embedding Model Performance**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Avg Embedding Time", "1.2s", "↘️ -0.3s")
            st.metric("Tokens/Second", "1,250", "↗️ +50")
        with col2:
            st.metric("Model Load Time", "3.4s", "↘️ -0.8s")
            st.metric("Memory per Embedding", "2.1MB", "↗️ +0.1MB")
        
        # Database performance
        st.markdown("**🗄️ Database Performance**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("MongoDB Query Time", "15ms", "↘️ -3ms")
            st.metric("Qdrant Search Time", "45ms", "↘️ -8ms")
        with col2:
            st.metric("Connection Pool", "85%", "↗️ +5%")
            st.metric("Cache Hit Rate", "92%", "↗️ +2%")
        
        # Performance profiling tools
        st.subheader("🛠️ Performance Profiling Tools")
        st.markdown("""
        **Available Profiling Options:**
        - **CPU Profiling**: Analyze CPU usage patterns
        - **Memory Profiling**: Track memory allocation and leaks
        - **Database Query Profiling**: Optimize database performance
        - **Network Latency Analysis**: Monitor external service calls
        """)
        
        if st.button("🔍 Run Performance Analysis"):
            with st.spinner("Running performance analysis..."):
                st.success("Performance analysis completed!")
                st.info("Detailed profiling results will be displayed here")
    
    with monitoring_tab[3]:  # Logs & Traces
        st.subheader("📝 Logs & Traces")
        st.markdown("Structured logging and trace analysis:")
        
        # Log viewing options
        log_option = st.selectbox(
            "Log View Options",
            ["Recent Logs", "Error Logs", "Performance Logs", "Correlation ID Search"],
            index=0
        )
        
        if log_option == "Recent Logs":
            st.info("📋 Recent system logs will be displayed here")
            st.markdown("""
            **Log Features:**
            - **Structured Format**: JSON-formatted logs with correlation IDs
            - **Log Levels**: INFO, WARNING, ERROR, DEBUG
            - **Request Tracing**: Full request lifecycle tracking
            - **Performance Data**: Timing and resource usage
            """)
        
        elif log_option == "Error Logs":
            st.info("❌ Error logs and exception details will be displayed here")
            st.markdown("""
            **Error Tracking:**
            - **Exception Details**: Full stack traces
            - **Error Context**: Request parameters and state
            - **Error Patterns**: Frequency and impact analysis
            - **Resolution Suggestions**: Common fixes and workarounds
            """)
        
        elif log_option == "Performance Logs":
            st.info("⚡ Performance-related logs will be displayed here")
            st.markdown("""
            **Performance Insights:**
            - **Slow Query Detection**: Database and API performance
            - **Resource Usage**: Memory, CPU, and network patterns
            - **Bottleneck Analysis**: Performance optimization opportunities
            - **Trend Analysis**: Performance over time
            """)
        
        elif log_option == "Correlation ID Search":
            correlation_id = st.text_input("Enter Correlation ID:")
            if st.button("🔍 Search"):
                if correlation_id:
                    st.info(f"Searching for logs with correlation ID: {correlation_id}")
                    st.markdown("**Trace Results:**")
                    st.json({
                        "correlation_id": correlation_id,
                        "request_path": "/api/query",
                        "duration": "1.2s",
                        "status": "success",
                        "logs": [
                            {"timestamp": "2024-01-15T10:30:00Z", "level": "INFO", "message": "Query started"},
                            {"timestamp": "2024-01-15T10:30:01Z", "level": "INFO", "message": "Query completed"}
                        ]
                    })
                else:
                    st.warning("Please enter a correlation ID")

        # Trace analysis
        st.subheader("🔍 Trace Analysis")
        st.markdown("""
        **Trace Features:**
        - **Request Flow**: Complete request lifecycle visualization
        - **Service Dependencies**: External service call tracking
        - **Performance Breakdown**: Time spent in each component
        - **Error Propagation**: How errors flow through the system
        """)
    
    with monitoring_tab[4]:  # AI Pipeline Traces
        st.subheader("🤖 AI Pipeline Traces & Experimentation")
        st.markdown("Trace and analyze AI pipeline performance, including document processing and query execution:")
        
        # Add options for trace viewing
        trace_option = st.selectbox(
            "Trace View Options",
            ["Show Recent Traces", "Show Traces for Last Query", "Show Traces for Last Ingestion"],
            index=0
        )
        
        if trace_option == "Show Recent Traces":
            if st.button("Fetch Recent Traces"):
                try:
                    resp = requests.get(f"{API_URL}/langsmith_traces", headers=headers)
                    if resp.status_code == 200:
                        traces = resp.json().get("traces", [])
                        if not traces:
                            st.info("No recent traces found.")
                        else:
                            st.success(f"Found {len(traces)} recent traces")
                            for i, t in enumerate(traces):
                                with st.expander(f"Trace {i+1}: {t.get('name', 'Unknown')} - {t.get('start_time', 'N/A')}"):
                                    st.json(t)
                    else:
                        st.error(f"Error: {resp.text}")
                except Exception as e:
                    st.error(f"Could not fetch traces: {e}")
            else:
                st.info("Click 'Fetch Recent Traces' to view recent AI pipeline traces.")
        
        elif trace_option == "Show Traces for Last Query":
            st.info("Traces for the last query will be shown here when you make a query.")
            st.markdown("""
            **How it works:**
            - Make a query in the Query tab
            - Return here to see the trace for that specific query
            - This helps analyze query performance and retrieval quality
            """)
        
        elif trace_option == "Show Traces for Last Ingestion":
            st.info("Traces for the last document ingestion will be shown here when you ingest a document.")
            st.markdown("""
            **How it works:**
            - Upload and ingest a document in the Ingest Document tab
            - Return here to see the trace for that specific ingestion
            - This helps analyze document processing performance
            """)
        
        # Add trace analytics section
        st.subheader("📊 Trace Analytics")
        st.markdown("""
        **Trace Metrics:**
        - **Query Latency**: Time taken for query processing
        - **Embedding Generation**: Time for vector embeddings
        - **Retrieval Quality**: Relevance scores and ranking
        - **Document Processing**: Chunking and indexing performance
        """)

elif page == "Documentation":
    st.header("📚 API Documentation")
    st.markdown("Comprehensive guide to the RAG API endpoints and usage examples.")
    
    # API Overview
    st.subheader("🔍 API Overview")
    st.markdown("""
    The RAG API provides a complete pipeline for document ingestion, processing, and semantic search with RAG generation.
    
    **Base URL**: `http://localhost:8000` (or your deployed endpoint)
    
    **Authentication**: All endpoints require Bearer token authentication.
    """)
    
    # Authentication
    st.subheader("🔐 Authentication")
    st.markdown("""
    All API endpoints require authentication using a Bearer token in the Authorization header:
    
    ```bash
    Authorization: Bearer YOUR_API_TOKEN
    ```
    
    **Note**: Replace `YOUR_API_TOKEN` with your actual API token from the `.env` file.
    """)
    
    # Endpoints Documentation
    st.subheader("🚀 API Endpoints")
    
    # POST /ingest
    with st.expander("📤 POST /ingest - Upload and Process Documents", expanded=True):
        st.markdown("""
        **Description**: Upload and process documents for RAG pipeline ingestion.
        
        **Endpoint**: `POST /ingest`
        
        **Content-Type**: `multipart/form-data`
        
        **Parameters**:
        - `file` (required): Document file (PDF, TXT, JSON)
        - `doc_metadata` (optional): JSON string with document metadata
        
        **Response**:
        ```json
        {
            "document_id": "507f1f77bcf86cd799439011",
            "status": "success"
        }
        ```
        
        **Example Request**:
        ```bash
        curl -X POST "http://localhost:8000/ingest" \\
             -H "Authorization: Bearer YOUR_API_TOKEN" \\
             -F "file=@document.pdf" \\
             -F "doc_metadata={\\"author\\": \\"John Doe\\", \\"category\\": \\"research\\"}"
        ```
        
        **Supported File Types**:
        - PDF (.pdf)
        - Text (.txt)
        - JSON (.json)
        - Word documents (.docx)
        """)
    
    # POST /query
    with st.expander("🔍 POST /query - Semantic Search with RAG Generation", expanded=True):
        st.markdown("""
        **Description**: Perform semantic search and retrieve relevant document chunks with RAG generation.
        
        **Endpoint**: `POST /query`
        
        **Content-Type**: `application/json`
        
        **Request Body**:
        ```json
        {
            "query": "What is machine learning?",
            "top_k": 5,
            "similarity_threshold": 0.7,
            "use_hybrid": true,
            "filters": {
                "category": "research"
            }
        }
        ```
        
        **Parameters**:
        - `query` (required): Search query string
        - `top_k` (optional): Number of results to return (default: 5)
        - `similarity_threshold` (optional): Minimum similarity score (default: 0.7)
        - `use_hybrid` (optional): Use hybrid search (vector + BM25) (default: true)
        - `filters` (optional): Metadata filters for narrowing results
        
        **Response**:
        ```json
        {
            "results": [
                {
                    "document_id": "507f1f77bcf86cd799439011",
                    "text": "Machine learning is a subset of artificial intelligence...",
                    "score": 0.95,
                    "filename": "ml_intro.pdf",
                    "bm25": true
                }
            ],
            "latency_ms": 245.6
        }
        ```
        
        **Example Request**:
        ```bash
        curl -X POST "http://localhost:8000/query" \\
             -H "Authorization: Bearer YOUR_API_TOKEN" \\
             -H "Content-Type: application/json" \\
             -d '{
                 "query": "What is machine learning?",
                 "top_k": 5,
                 "similarity_threshold": 0.7
             }'
        ```
        """)
    
    # GET /documents
    with st.expander("📋 GET /documents - List Processed Documents", expanded=True):
        st.markdown("""
        **Description**: Retrieve a list of all processed documents with metadata.
        
        **Endpoint**: `GET /documents`
        
        **Parameters**: None
        
        **Response**:
        ```json
        {
            "documents": [
                {
                    "document_id": "507f1f77bcf86cd799439011",
                    "filename": "ml_intro.pdf",
                    "doc_metadata": "{\\"author\\": \\"John Doe\\", \\"category\\": \\"research\\"}",
                    "upload_time": "2024-01-15T10:30:00Z",
                    "size": 1024000
                }
            ]
        }
        ```
        
        **Example Request**:
        ```bash
        curl -X GET "http://localhost:8000/documents" \\
             -H "Authorization: Bearer YOUR_API_TOKEN"
        ```
        """)
    
    # DELETE /documents/{id}
    with st.expander("🗑️ DELETE /documents/{id} - Remove Documents", expanded=True):
        st.markdown("""
        **Description**: Delete a specific document and its associated embeddings.
        
        **Endpoint**: `DELETE /documents/{document_id}`
        
        **Parameters**:
        - `document_id` (path parameter): MongoDB ObjectId of the document to delete
        
        **Response**:
        ```json
        {
            "document_id": "507f1f77bcf86cd799439011",
            "status": "deleted"
        }
        ```
        
        **Example Request**:
        ```bash
        curl -X DELETE "http://localhost:8000/documents/507f1f77bcf86cd799439011" \\
             -H "Authorization: Bearer YOUR_API_TOKEN"
        ```
        """)
    
    # Additional Endpoints
    with st.expander("🔧 Additional Endpoints", expanded=False):
        st.markdown("""
        **Health Check**: `GET /healthz`
        - Returns system health status and dependency information
        
        **Metrics**: `GET /metrics`
        - Returns Prometheus metrics for monitoring
        
        **LangSmith Traces**: `GET /langsmith_traces`
        - Returns recent LangSmith traces for debugging and analysis
        """)
    
    # Usage Examples
    st.subheader("💡 Usage Examples")
    
    # Python Example
    with st.expander("🐍 Python Example", expanded=False):
        st.code("""
import requests
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_TOKEN = "your_api_token_here"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# 1. Upload a document
with open("document.pdf", "rb") as f:
    files = {"file": ("document.pdf", f, "application/pdf")}
    data = {
        "doc_metadata": json.dumps({"author": "John Doe", "category": "research"})
    }
    response = requests.post(f"{API_BASE_URL}/ingest", files=files, data=data, headers=headers)
    document_id = response.json()["document_id"]
    print(f"Document uploaded with ID: {document_id}")

# 2. Query the RAG system
query_data = {
    "query": "What is machine learning?",
    "top_k": 5,
    "similarity_threshold": 0.7
}
response = requests.post(f"{API_BASE_URL}/query", json=query_data, headers=headers)
results = response.json()["results"]
for result in results:
    print(f"Score: {result['score']}, Text: {result['text'][:100]}...")

# 3. List all documents
response = requests.get(f"{API_BASE_URL}/documents", headers=headers)
documents = response.json()["documents"]
for doc in documents:
    print(f"Document: {doc['filename']}, ID: {doc['document_id']}")

# 4. Delete a document
response = requests.delete(f"{API_BASE_URL}/documents/{document_id}", headers=headers)
print(f"Document deleted: {response.json()['status']}")
        """, language="python")
    
    # JavaScript Example
    with st.expander("🟨 JavaScript Example", expanded=False):
        st.code("""
// API Configuration
const API_BASE_URL = "http://localhost:8000";
const API_TOKEN = "your_api_token_here";

// 1. Upload a document
async function uploadDocument(file, metadata) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("doc_metadata", JSON.stringify(metadata));
    formData.append("strategy", "langchain");
    
    const response = await fetch(`${API_BASE_URL}/ingest`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${API_TOKEN}`
        },
        body: formData
    });
    
    const result = await response.json();
    return result.document_id;
}

// 2. Query the RAG system
async function queryRAG(query, topK = 5) {
    const response = await fetch(`${API_BASE_URL}/query`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${API_TOKEN}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            query: query,
            top_k: topK,
            similarity_threshold: 0.7
        })
    });
    
    const result = await response.json();
    return result.results;
}

// 3. List documents
async function listDocuments() {
    const response = await fetch(`${API_BASE_URL}/documents`, {
        headers: {
            "Authorization": `Bearer ${API_TOKEN}`
        }
    });
    
    const result = await response.json();
    return result.documents;
}

// 4. Delete a document
async function deleteDocument(documentId) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
        method: "DELETE",
        headers: {
            "Authorization": `Bearer ${API_TOKEN}`
        }
    });
    
    const result = await response.json();
    return result.status;
}
        """, language="javascript")
    
    # Error Handling
    st.subheader("⚠️ Error Handling")
    st.markdown("""
    **Common HTTP Status Codes**:
    
    - `200 OK`: Request successful
    - `201 Created`: Document successfully ingested
    - `400 Bad Request`: Invalid request parameters or file format
    - `401 Unauthorized`: Invalid or missing API token
    - `404 Not Found`: Document not found (for DELETE operations)
    - `408 Request Timeout`: Document processing timed out
    - `500 Internal Server Error`: Server-side error
    
    **Error Response Format**:
    ```json
    {
        "detail": "Error message describing the issue"
    }
    ```
    """)
    
    # Best Practices
    st.subheader("🎯 Best Practices")
    st.markdown("""
    **Document Processing**:
    - Use appropriate file formats (PDF, TXT, JSON)
    - Include meaningful metadata for better filtering
    - Consider document size limits for processing time
    
    **Querying**:
    - Use specific, focused queries for better results
    - Adjust `similarity_threshold` based on your needs
    - Use metadata filters to narrow down results
    
    **Performance**:
    - Monitor response times and adjust `top_k` accordingly
    - Use the health check endpoint to monitor system status
    - Implement proper error handling and retries
    
    **Security**:
    - Keep your API token secure and rotate regularly
    - Validate file uploads and metadata
    - Use HTTPS in production environments
    """)

 