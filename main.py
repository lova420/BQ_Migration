import streamlit as st
from google.generativeai import GenerativeModel, configure
from google.generativeai.types import GenerationConfig
import hashlib
from functools import lru_cache
import uuid
import base64
import pyperclip  # For clipboard functionality

st.set_page_config(
    page_title="Oracle to Snowflake DDL Converter & Validator",
    page_icon=":snowflake:",
    layout="wide",
)

# Modern Glass UI CSS
custom_css = """
<style>
    :root {
        --primary: #6C5CE7;
        --secondary: #00CEC9;
        --dark: #2D3436;
        --light: #F5F6FA;
        --success: #00B894;
        --warning: #FDCB6E;
        --error: #D63031;
    }
    
    .main {
        background: rgba(245, 247, 250, 0.85) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, rgba(197, 222, 245, 0.8) 0%, rgba(195, 207, 226, 0.8) 100%) !important;
    }
    
    .stTitle {
        color: var(--dark) !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        text-align: center;
        padding: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .stSubheader {
        color: var(--dark) !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        padding: 0.5rem;
    }
    
    .stButton>button {
        background: linear-gradient(45deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1.5rem !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(5px) !important;
        background-color: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
        background: linear-gradient(45deg, #5D4AE3, #00B8B5) !important;
    }
    
    .stFileUploader>div {
        background: rgba(255, 255, 255, 0.7) !important;
        padding: 1.5rem !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .stCodeBlock {
        background: rgba(44, 62, 80, 0.9) !important;
        border-radius: 15px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.7) !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        padding: 1rem !important;
    }
    
    .stRadio>div {
        background: rgba(255, 255, 255, 0.7) !important;
        border-radius: 15px !important;
        padding: 1rem !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .stSuccess {
        background: rgba(0, 184, 148, 0.8) !important;
        color: white !important;
        padding: 1rem !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .stError {
        background: rgba(214, 48, 49, 0.8) !important;
        color: white !important;
        padding: 1rem !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .stWarning {
        background: rgba(253, 203, 110, 0.8) !important;
        color: var(--dark) !important;
        padding: 1rem !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .stSpinner>div {
        border-color: var(--primary) !important;
    }
    
    .download-button {
        background: linear-gradient(45deg, var(--success), #00A884) !important;
        color: white !important;
        padding: 12px 24px !important;
        text-align: center !important;
        text-decoration: none !important;
        display: inline-block !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        margin: 8px 4px !important;
        cursor: pointer !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(5px) !important;
        background-color: rgba(0, 184, 148, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .download-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
        background: linear-gradient(45deg, #00A884, #009975) !important;
    }
    
    /* Glass card effect for output */
    .output-card {
        background: rgba(255, 255, 255, 0.7) !important;
        border-radius: 15px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #5D4AE3;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# Initialize session state
if 'snowflake_ddl' not in st.session_state:
    st.session_state.snowflake_ddl = None

# Google API Key (Consider using st.secrets)
GOOGLE_API_KEY = "AIzaSyC21Bks56EKnmNz1uoeabQzHo4FwN7XMyI"
configure(api_key=GOOGLE_API_KEY)

@lru_cache(maxsize=32)
def get_model():
    generation_config = GenerationConfig(temperature=0.3)
    return GenerativeModel(model_name="gemini-2.0-flash"), generation_config

def split_ddl_into_blocks(ddl):
    if not ddl:
        return []
    blocks = ddl.strip().split("\n\n")
    return [block.strip() for block in blocks if block.strip()]

def clean_sql_response(response_text):
    if not response_text:
        return ""
    
    # Remove code block markers and any leading/trailing whitespace
    cleaned_text = response_text.replace("```sql", "").replace("```", "").strip()
    
    # Remove any explanatory text that might precede the SQL
    if "Snowflake DDL:" in cleaned_text:
        cleaned_text = cleaned_text.split("Snowflake DDL:")[1].strip()
    
    return cleaned_text

def convert_to_snowflake(oracle_ddl):
    model, generation_config = get_model()
    
    blocks = split_ddl_into_blocks(oracle_ddl)
    snowflake_ddl_chunks = []
    
    for i, block in enumerate(blocks):
        block_hash = hashlib.md5(block.encode()).hexdigest()
        
        prompt = f"""
        You are a SQL expert specializing in converting Oracle DDL to Snowflake DDL.
        Given the following Oracle DDL block, convert it to equivalent Snowflake DDL.
        Preserve object names and basic structure. Focus on data type conversion and syntax differences.
        Return only the Snowflake DDL, no extra text.

        Oracle DDL Block:
        ```sql
        {block}
        ```

        Note: While creating the table DDLs, please handle the following points with alternative approaches:
           1. UNIQUE INDEX -> Unique Constraints (Informational, no enforcement) or ETL logic for uniqueness enforcement.
           2. PARTITION BY RANGE -> Clustering Keys with Micro-partitioning.
           3. BITMAP INDEX -> Clustering Keys and Query Pruning.
           These are not supported in Snowflake.
        """
        try:
            response = model.generate_content(prompt, generation_config=generation_config)
            if response and response.text:
                cleaned_response = clean_sql_response(response.text)
                if cleaned_response:
                    snowflake_ddl_chunks.append(cleaned_response)
                else:
                    st.warning(f"Empty response after cleaning for block {i + 1}")
            else:
                st.warning(f"Empty response for block {i + 1}")
        except Exception as e:
            st.error(f"Error during DDL conversion of block {i + 1}: {str(e)}")
            continue

    if not snowflake_ddl_chunks:
        st.error("No valid Snowflake DDL was generated.")
        return None

    snowflake_ddl = "\n\n".join(snowflake_ddl_chunks)
    return snowflake_ddl

def create_download_button(object_to_download, download_filename, button_text):
    try:
        b64 = base64.b64encode(object_to_download.encode()).decode()
    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = f'download-button-{button_uuid}'

    custom_css = f"""
        <style>
            #{button_id} {{
                background: linear-gradient(45deg, var(--success), #00A884) !important;
                color: white !important;
                padding: 12px 24px !important;
                text-align: center !important;
                text-decoration: none !important;
                display: inline-block !important;
                font-size: 16px !important;
                font-weight: 600 !important;
                margin: 8px 4px !important;
                cursor: pointer !important;
                border-radius: 12px !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
                backdrop-filter: blur(5px) !important;
                background-color: rgba(0, 184, 148, 0.2) !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
            }}
            #{button_id}:hover {{
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
                background: linear-gradient(45deg, #00A884, #009975) !important;
            }}
        </style> """

    dl_link = custom_css + f"""
    <a download="{download_filename}" id="{button_id}" href="data:text/sql;base64,{b64}">
        {button_text}
    </a><br><br>
    """
    return dl_link
st.title("MigrateIQ")
st.subheader("Convert Oracle DDL to Snowflake DDL")



# Input Options
input_option = st.radio(
    "Select Input Method:", 
    ["File Upload", "Text Area"],
    horizontal=True
)

file_content = None
text_area_content = None

if input_option == "File Upload":
    uploaded_file = st.file_uploader(
        "Upload Oracle DDL File", 
        type=["sql", "txt"],
        help="Upload a .sql or .txt file containing Oracle DDL statements"
    )
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode('utf-8', errors='replace')
        except Exception as e:
            st.error(f"Error reading the uploaded file: {e}")
            file_content = None
else:
    text_area_content = st.text_area(
        "Paste Oracle DDL here:",
        height=300,
        placeholder="""CREATE TABLE employees (
    emp_id NUMBER PRIMARY KEY,
    emp_name VARCHAR2(100),
    hire_date DATE,
    salary NUMBER(10,2)
);"""
    )

# Determine which content to use
oracle_ddl = file_content if input_option == "File Upload" else text_area_content

if oracle_ddl and st.button("Convert to Snowflake", type="primary"):
    if not GOOGLE_API_KEY:
        st.error("Please enter your Google API key.")
    else:
        with st.spinner("🔮 Converting Oracle DDL to Snowflake..."):
            st.session_state.snowflake_ddl = convert_to_snowflake(oracle_ddl)

        if st.session_state.snowflake_ddl:
            st.subheader("Generated Snowflake DDL")
            
            # Display the code with copy button
            st.code(st.session_state.snowflake_ddl, language="sql")
            
            col1, col2 = st.columns(2)
            
            with col2:
                uploaded_filename = "converted_snowflake.sql"
                if input_option == "File Upload" and uploaded_file is not None:
                    uploaded_filename = f"{uploaded_file.name.split('.')[0]}_snowflake.sql"
                
                st.markdown(
                    create_download_button(
                        st.session_state.snowflake_ddl,
                        uploaded_filename,
                        "💾 Download Snowflake DDL"
                    ),
                    unsafe_allow_html=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)