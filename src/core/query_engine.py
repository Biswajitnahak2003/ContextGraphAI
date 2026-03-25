import os
from groq import Groq
from dotenv import load_dotenv
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class QueryEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant"

    def _get_system_prompt(self, context_data):
        return f"""
        You are Dodge AI, an expert Graph Agent for SAP Order-to-Cash (O2C) processes.
        Your task is to answer user questions based ONLY on the provided graph context.
        
        Context Data (Nodes and Edges):
        {json.dumps(context_data, indent=2)}
        
        Rules:
        1. If the answer is not in the context, say "I don't have enough information in the current graph to answer that."
        2. Be concise and professional.
        3. Use document numbers (Sales Order, Delivery, etc.) as identifiers.
        4. If the user asks for a status, look at the connections (e.g., if a Billing Document exists, it's likely invoiced).
        """

    def process_query(self, user_query, graph_manager):
        import re
        doc_ids = re.findall(r'\b\d{6,10}\b', user_query)
        
        context_data = {"nodes": [], "edges": []}
        seen_nodes = set()
        
        if doc_ids:
            for doc_id in doc_ids:
                subgraph = graph_manager.get_subgraph_for_order(doc_id)
                if subgraph:
                    # Limit to top 50 nodes to avoid token overflow
                    for i, (node, attrs) in enumerate(subgraph.nodes(data=True)):
                        if i > 50: break
                        if node not in seen_nodes:
                            # Only send key attributes to save tokens
                            essential_attrs = {k: v for k, v in attrs.items() if k in ['type', 'label', 'totalNetAmount', 'postingDate', 'billingDocumentDate', 'creationDate']}
                            context_data["nodes"].append({"id": node, "attrs": essential_attrs})
                            seen_nodes.add(node)
                    
                    for i, (u, v, attrs) in enumerate(subgraph.edges(data=True)):
                        if i > 50: break
                        context_data["edges"].append({"from": u, "to": v, "label": attrs.get('label')})

        if not context_data["nodes"]:
            return "I couldn't find any relevant document numbers in your query. Please provide a Sales Order, Delivery, or Billing ID to analyze (e.g., 740556)."

        # 2. Call Groq
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self._get_system_prompt(context_data)},
                {"role": "user", "content": user_query}
            ],
            model=self.model,
            max_tokens=1024
        )
        
        return chat_completion.choices[0].message.content

if __name__ == "__main__":
    from graph_manager import GraphManager
    gm = GraphManager()
    gm.build_graph()
    qe = QueryEngine()
    # Example query (ensure this SO exists in your DB)
    resp = qe.process_query("What is the status of Sales Order 740506?", gm)
    print(resp)
