import streamlit as st
import streamlit.components.v1 as components
import requests
from pyvis.network import Network
import os
import tempfile
import json
import re

# Page Config
st.set_page_config(page_title="Context Graph AI - SAP O2C", layout="wide")

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Custom CSS - target Streamlit's actual elements, no wrapper divs
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Outfit:wght@400;700&display=swap');
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; color: #0f172a; }
    /* Remove Streamlit's default massive top padding */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    /* Chat text must always be dark */
    div[data-testid="stChatMessage"] { color: #0f172a !important; }
    div[data-testid="stMarkdownContainer"] p { color: #0f172a !important; }
    h3 { color: #0f172a !important; }
    span { color: #0f172a !important; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_so_id" not in st.session_state:
    st.session_state.active_so_id = None

# Header
st.markdown("**Mapping** &nbsp; Order to Cash")

# Layout
col_graph, col_chat = st.columns([7, 3], gap="medium")

with col_graph:
    try:
        params = {"so_id": st.session_state.active_so_id} if st.session_state.active_so_id else {}
        response = requests.get(f"{API_URL}/graph", params=params, timeout=30)
        if response.status_code == 200:
            graph_data = response.json()

            net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#334155")

            COLORS = {
                'SalesOrder': '#3b82f6', 'Customer': '#ef4444', 'Product': '#10b981',
                'Delivery': '#f59e0b', 'BillingDocument': '#8b5cf6',
                'AccountingDocument': '#ec4899', 'Payment': '#06b6d4'
            }

            for n in graph_data["nodes"]:
                ntype = n["attrs"].get('type', 'Other')
                color = COLORS.get(ntype, '#94a3b8')
                net.add_node(n["id"], label=f"{ntype}\n{n['id']}", title=f"<b>{ntype}</b>: {n['id']}<br>{json.dumps(n['attrs'])}", color=color, size=25, shape="dot")

            for e in graph_data["edges"]:
                net.add_edge(e["source"], e["target"], title=e["label"], color="#e2e8f0", width=1.5, arrows="to")

            net.set_options('{"physics": {"solver": "forceAtlas2Based", "forceAtlas2Based": {"gravitationalConstant": -60}, "stabilization": {"iterations": 200}}}')

            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                net.save_graph(tmp.name)
                with open(tmp.name, 'r', encoding='utf-8') as f:
                    html = f.read()
                components.html(html, height=600)
        else:
            st.error("Failed to load graph data from API.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

with col_chat:
    st.markdown("### Chat with Graph")
    st.caption("Order to Cash")

    if st.session_state.active_so_id:
        if st.button("Reset Graph View"):
            st.session_state.active_so_id = None
            st.rerun()

    chat_subcontainer = st.container(height=450, border=False)
    with chat_subcontainer:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Analyze anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Extract ID for filtering
        doc_ids = re.findall(r'\d{6,10}', prompt)
        if doc_ids:
            st.session_state.active_so_id = doc_ids[0]

        # Call API for LLM response
        try:
            resp = requests.post(f"{API_URL}/query", json={"user_query": prompt}, timeout=60)
            if resp.status_code == 200:
                answer = resp.json()["response"]
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                error_detail = resp.text
                st.session_state.messages.append({"role": "assistant", "content": f"API Error ({resp.status_code}): {error_detail}"})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Connection Error: {e}"})

        st.rerun()
