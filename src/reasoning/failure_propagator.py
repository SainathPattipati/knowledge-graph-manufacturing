"""
Failure propagation analysis for impact assessment.

Traces failure cascades through equipment connectivity and failure relationships.
"""

from typing import Dict, List, Set
from dataclasses import dataclass
import networkx as nx


@dataclass
class FailureImpact:
    """Result of failure impact analysis."""
    initial_equipment: str
    directly_affected: List[str]
    cascade_affected: List[str]
    total_affected: int
    critical_path: List[str]
    affected_products: List[str]
    estimated_downtime_hours: float


class FailurePropagator:
    """Analyze failure cascade paths and impact scope."""
    
    def __init__(self, graph_connector):
        """
        Initialize failure propagator.
        
        Args:
            graph_connector: Neo4jConnector instance
        """
        self.graph = graph_connector
        self.local_graph: nx.DiGraph | None = None
    
    def _build_local_graph(self) -> None:
        """Build NetworkX graph from Neo4j for analysis."""
        self.local_graph = nx.DiGraph()
        
        # Query all nodes
        nodes_query = """
        MATCH (n)
        WHERE n.id IS NOT NULL
        RETURN n.id as id, labels(n)[0] as label, n
        """
        
        nodes = self.graph.execute_query(nodes_query)
        for node in nodes:
            self.local_graph.add_node(node["id"], label=node["label"])
        
        # Query all relationships
        rels_query = """
        MATCH (a)-[r]->(b)
        RETURN a.id as source, b.id as target, type(r) as rel_type
        """
        
        rels = self.graph.execute_query(rels_query)
        for rel in rels:
            # Add edges for failure propagation
            if rel["rel_type"] in ["CAUSES_FAILURE", "CONNECTED_TO", "PART_OF", "HAS_COMPONENT"]:
                self.local_graph.add_edge(rel["source"], rel["target"], type=rel["rel_type"])
    
    def analyze_failure(self, equipment_id: str, max_depth: int = 5) -> FailureImpact:
        """
        Analyze failure impact propagation.
        
        Args:
            equipment_id: ID of failed equipment
            max_depth: Maximum cascade depth to analyze
        
        Returns:
            FailureImpact with affected equipment and products
        """
        if not self.local_graph:
            self._build_local_graph()
        
        directly_affected = set()
        cascade_affected = set()
        
        # BFS to find all reachable nodes
        queue = [(equipment_id, 0)]
        visited = {equipment_id}
        
        while queue:
            node_id, depth = queue.pop(0)
            
            if depth == 0:
                directly_affected.add(node_id)
            elif depth <= max_depth:
                cascade_affected.add(node_id)
            
            if depth < max_depth and node_id in self.local_graph:
                for neighbor in self.local_graph.successors(node_id):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, depth + 1))
        
        # Find critical path (longest path)
        try:
            critical_path = nx.dag_longest_path(self.local_graph, equipment_id)
        except (nx.NodeNotFound, nx.NetworkXError):
            critical_path = [equipment_id]
        
        # Get affected products
        affected_products = self._get_affected_products(visited)
        
        # Estimate downtime
        downtime_hours = self._estimate_downtime(directly_affected)
        
        return FailureImpact(
            initial_equipment=equipment_id,
            directly_affected=list(directly_affected),
            cascade_affected=list(cascade_affected),
            total_affected=len(visited),
            critical_path=critical_path,
            affected_products=affected_products,
            estimated_downtime_hours=downtime_hours
        )
    
    def _get_affected_products(self, affected_equipment_ids: Set[str]) -> List[str]:
        """Get list of products affected by equipment failure."""
        # Query products manufactured by affected equipment
        query = """
        MATCH (p:Material)<-[:PRODUCED_BY]-(e)
        WHERE e.id IN $equipment_ids
        RETURN DISTINCT p.id as product_id
        """
        
        results = self.graph.execute_query(query, {"equipment_ids": list(affected_equipment_ids)})
        return [r["product_id"] for r in results]
    
    def _estimate_downtime(self, affected_equipment_ids: Set[str]) -> float:
        """Estimate downtime from MTBF of affected equipment."""
        total_downtime = 0.0
        
        for equip_id in affected_equipment_ids:
            query = "MATCH (e {id: $id}) RETURN e.mtbf_hours as mtbf"
            results = self.graph.execute_query(query, {"id": equip_id})
            
            if results and results[0]["mtbf"]:
                # Estimate 10% of MTBF as expected downtime
                total_downtime += results[0]["mtbf"] * 0.1
        
        return total_downtime
    
    def find_minimal_cut_set(self, equipment_id: str) -> List[Set[str]]:
        """
        Find minimal cut sets (minimal sets of failures causing shutdown).
        
        Returns critical components whose failure would stop production.
        """
        if not self.local_graph:
            self._build_local_graph()
        
        # Simplified: find nodes with high in-degree in critical path
        critical_nodes = []
        
        for node in self.local_graph.nodes():
            in_degree = self.local_graph.in_degree(node)
            out_degree = self.local_graph.out_degree(node)
            
            # High in-degree + low out-degree = bottleneck
            if in_degree > 2 and out_degree > 2:
                critical_nodes.append(node)
        
        return [set(critical_nodes)]
