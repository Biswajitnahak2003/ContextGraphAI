import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class QueryEngine:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.gemini_api_key and not self.openrouter_api_key:
            raise ValueError("Neither GEMINI_API_KEY nor OPENROUTER_API_KEY found in environment variables.")

        if self.gemini_api_key:
            # Use direct Gemini API (extremely high limits, very robust)
            self.model = "gemini-2.5-flash"
            print(f"[QueryEngine] Using Direct Gemini API ({self.model})")
        else:
            # Fallback to OpenRouter (using Llama 3.3 70B which has multiple providers to prevent rate limits)
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key
            )
            self.model = "meta-llama/llama-3.3-70b-instruct:free"
            print(f"[QueryEngine] Using OpenRouter API ({self.model})")

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
        doc_ids = re.findall(r'\d{6,10}', user_query)
        
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

        # Route request based on API Key presence
        if self.gemini_api_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user_query}]
                    }
                ],
                "systemInstruction": {
                    "parts": [{"text": self._get_system_prompt(context_data)}]
                },
                "generationConfig": {
                    "maxOutputTokens": 1024,
                    "temperature": 0.2
                }
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    res_json = response.json()
                    try:
                        return res_json["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError):
                        return f"Gemini API returned an unexpected response format: {json.dumps(res_json)}"
                else:
                    return f"Gemini API Error ({response.status_code}): {response.text}"
            except Exception as e:
                return f"Failed to connect to Gemini API: {str(e)}"
        else:
            # Call OpenRouter
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
