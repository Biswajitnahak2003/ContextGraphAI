import streamlit as st
import streamlit.components.v1 as components
import requests
from pyvis.network import Network
import os
import tempfile
import json

# Page Config
st.set_page_config(page_title="Context Graph AI - SAP O2C", layout="wide")

API_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Outfit:wght@400;700&display=swap');
    .stApp { background-color: #fcfcfd; font-family: 'Inter', sans-serif; }
    .header { font-family: 'Outfit', sans-serif; font-size: 20px; color: #0f172a; padding: 15px 20px; border-bottom: 1px solid #f1f5f9; margin-bottom: 25px; display: flex; align-items: center; background: white; }
    .badge { background: #f1f5f9; color: #64748b; padding: 2px 10px; border-radius: 6px; font-size: 12px; margin-right: 15px; }
    .chat-container { background: white; border-radius: 16px; padding: 24px; border: 1px solid #f1f5f9; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.05); height: 85vh; display: flex; flex-direction: column; }
    .graph-container { background: white; border-radius: 16px; border: 1px solid #f1f5f9; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.05); height: 85vh; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_so_id" not in st.session_state:
    st.session_state.active_so_id = None

# UI Layout
st.markdown('<div class="header"><span class="badge">Mapping</span> Order to Cash</div>', unsafe_allow_html=True)

col_graph, col_chat = st.columns([7.2, 2.8], gap="large")

with col_graph:
    st.markdown('<div class="graph-container">', unsafe_allow_html=True)
    
    # Fetch Graph Data from API
    try:
        params = {"so_id": st.session_state.active_so_id} if st.session_state.active_so_id else {}
        response = requests.get(f"{API_URL}/graph", params=params)
        if response.status_code == 200:
            graph_data = response.json()
            
            net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="#334155")
            
            COLORS = {
                'SalesOrder': '#3b82f6', 'Customer': '#ef4444', 'Product': '#10b981', 
                'Delivery': '#f59e0b', 'BillingDocument': '#8b5cf6', 
                'AccountingDocument': '#ec4899', 'Payment': '#06b6d4'
            }
            
            for n in graph_data["nodes"]:
                ntype = n["attrs"].get('type', 'Other')
                color = COLORS.get(ntype, '#94a3b8')
                net.add_node(n["id"], label=f"{ntype}\n{n['id']}", title=f"<b>{ntype}</b>: {n['id']}<br>Details: {json.dumps(n['attrs'])}", color=color, size=25, shape="dot")
            
            for e in graph_data["edges"]:
                net.add_edge(e["source"], e["target"], title=e["label"], color="#e2e8f0", width=1.5, arrows="to")

            net.set_options('{"physics": {"solver": "forceAtlas2Based", "forceAtlas2Based": {"gravitationalConstant": -60}, "stabilization": {"iterations": 200}}}')

            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                net.save_graph(tmp.name)
                with open(tmp.name, 'r', encoding='utf-8') as f:
                    html = f.read()
                components.html(html, height=800)
        else:
            st.error("Failed to load graph data from API.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_chat:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown("### **Chat with Graph**")
    st.caption("Order to Cash")
    
    if st.session_state.active_so_id:
        if st.button("Reset Graph View"):
            st.session_state.active_so_id = None
            st.rerun()

    chat_subcontainer = st.container(height=550, border=False)
    with chat_subcontainer:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Analyze anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Extract ID for filtering
        import re
        doc_ids = re.findall(r'\d{6,10}', prompt)
        if doc_ids:
            st.session_state.active_so_id = doc_ids[0]

        # Call API for LLM response
        try:
            resp = requests.post(f"{API_URL}/query", json={"user_query": prompt})
            if resp.status_code == 200:
                answer = resp.json()["response"]
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.session_state.messages.append({"role": "assistant", "content": "API Error: Failed to process query."})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Connection Error: {e}"})
        
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
