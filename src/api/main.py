from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.core.graph_manager import GraphManager
from src.core.query_engine import QueryEngine
import uvicorn

from typing import List, Dict, Any, Optional

app = FastAPI(title="Context Graph AI API")

# Pydantic Models for Validation
class QueryRequest(BaseModel):
    user_query: str

class QueryResponse(BaseModel):
    response: str

class NodeAttrs(BaseModel):
    type: str
    label: str
    # Flexible container for SAP attributes
    attributes: Dict[str, Any]

class Node(BaseModel):
    id: str
    attrs: Dict[str, Any]

class Edge(BaseModel):
    source: str
    target: str
    label: str

class GraphResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

# Initialize managers
gm = GraphManager()
gm.build_graph()
qe = QueryEngine()

@app.get("/graph", response_model=GraphResponse)
async def get_graph(so_id: Optional[str] = None):
    """Returns graph nodes and edges. Optional filtering by Sales Order ID."""
    if so_id:
        sub = gm.get_subgraph_for_order(so_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Sales Order not found")
        graph_to_use = sub
    else:
        graph_to_use = gm.graph
        
    nodes = []
    for node, attrs in graph_to_use.nodes(data=True):
        nodes.append(Node(id=str(node), attrs=attrs))
        
    edges = []
    for u, v, attrs in graph_to_use.edges(data=True):
        edges.append(Edge(source=str(u), target=str(v), label=attrs.get('label', '')))
        
    return GraphResponse(nodes=nodes, edges=edges)

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Processes natural language queries via Groq."""
    response = qe.process_query(request.user_query, gm)
    return QueryResponse(response=response)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
