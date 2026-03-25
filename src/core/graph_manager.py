import sqlite3
import networkx as nx
import json

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "sap_o2c.db")

class GraphManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.graph = nx.MultiDiGraph()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def build_graph(self):
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Add Sales Order Nodes and Customer Nodes
        cursor.execute('SELECT * FROM sales_order_headers')
        for row in cursor.fetchall():
            so_id = row['salesOrder']
            cust_id = row['soldToParty']
            self.graph.add_node(so_id, type='SalesOrder', label=f"Order {so_id}", **dict(row))
            self.graph.add_node(cust_id, type='Customer', label=f"Customer {cust_id}")
            self.graph.add_edge(so_id, cust_id, label='PLACED_BY')

        # 2. Add Product Nodes and Link to Sales Orders
        cursor.execute('SELECT * FROM sales_order_items')
        for row in cursor.fetchall():
            so_id = row['salesOrder']
            prod_id = row['material']
            item_id = row['salesOrderItem']
            node_id = f"ITM_{so_id}_{item_id}"
            self.graph.add_node(prod_id, type='Product', label=f"Product {prod_id}")
            self.graph.add_edge(so_id, prod_id, label='CONTAINS', item=item_id, quantity=row['requestedQuantity'])

        # 3. Add Delivery Nodes and Link to Sales Orders
        cursor.execute('SELECT * FROM outbound_delivery_items')
        for row in cursor.fetchall():
            del_id = row['deliveryDocument']
            so_id = row['referenceSdDocument']
            if so_id:
                self.graph.add_node(del_id, type='Delivery', label=f"Delivery {del_id}")
                self.graph.add_edge(del_id, so_id, label='FULFILLS')

        # 4. Add Billing Document Nodes and Link to Deliveries
        cursor.execute('SELECT * FROM billing_document_items')
        for row in cursor.fetchall():
            bill_id = row['billingDocument']
            del_id = row['referenceSdDocument']
            if del_id:
                self.graph.add_node(bill_id, type='BillingDocument', label=f"Invoice {bill_id}")
                self.graph.add_edge(bill_id, del_id, label='INVOICES')

        # 5. Add Accounting Documents and Link to Billing
        cursor.execute('SELECT * FROM journal_entry_items_accounts_receivable')
        for row in cursor.fetchall():
            acc_id = row['accountingDocument']
            bill_id = row['referenceDocument']
            if bill_id:
                self.graph.add_node(acc_id, type='AccountingDocument', label=f"Journal {acc_id}")
                self.graph.add_edge(acc_id, bill_id, label='POSTED_FROM')

        # 6. Add Payments and Link to Accounting Documents
        cursor.execute('SELECT * FROM payments_accounts_receivable')
        for row in cursor.fetchall():
            pay_id = row['clearingAccountingDocument']
            acc_id = row['accountingDocument']
            if pay_id and acc_id and pay_id != acc_id:
                self.graph.add_node(pay_id, type='Payment', label=f"Payment {pay_id}")
                self.graph.add_edge(pay_id, acc_id, label='CLEARS')

        conn.close()
        return self.graph

    def get_subgraph_for_order(self, sales_order_id):
        # Extract related nodes for a specific order to keep visualization clean
        if sales_order_id not in self.graph:
            return None
        
        nodes = {sales_order_id}
        # Get neighbors (one level out)
        levels = 3
        current_nodes = {sales_order_id}
        for _ in range(levels):
            next_nodes = set()
            for node in current_nodes:
                if node in self.graph:
                    next_nodes.update(self.graph.neighbors(node))
                    next_nodes.update(self.graph.predecessors(node))
            nodes.update(next_nodes)
            current_nodes = next_nodes
            
        return self.graph.subgraph(nodes)

if __name__ == "__main__":
    gm = GraphManager()
    g = gm.build_graph()
    print(f"Graph built with {g.number_of_nodes()} nodes and {g.number_of_edges()} edges.")
