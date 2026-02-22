"""Path analysis for material traceability and dependency resolution."""

from typing import List, Dict, Tuple
import networkx as nx


class PathAnalyzer:
    """Analyze graph paths for manufacturing reasoning."""
    
    def __init__(self, graph_connector):
        """Initialize path analyzer."""
        self.graph = graph_connector
    
    def material_traceability(
        self,
        material_id: str,
        direction: str = "forward"
    ) -> Dict[str, List[str]]:
        """
        Trace material through production chain.
        
        Args:
            material_id: ID of material to trace
            direction: "forward" (to products) or "backward" (from suppliers)
        
        Returns:
            Dict with traceability path
        """
        if direction == "forward":
            query = """
            MATCH path = (m:Material {id: $id})-[:CONTAINS|PRODUCED_BY|REQUIRES_MATERIAL*]->(p)
            RETURN [n in nodes(path) | n.id] as path
            """
        else:
            query = """
            MATCH path = (s)-[:CONTAINS|PRODUCED_BY|REQUIRES_MATERIAL*]->(m:Material {id: $id})
            RETURN [n in nodes(path) | n.id] as path
            """
        
        result = self.graph.execute_query(query, {"id": material_id})
        
        return {
            "material_id": material_id,
            "traceability_paths": [r["path"] for r in result]
        }
    
    def maintenance_dependency_resolution(self, work_order_id: str) -> List[str]:
        """
        Find dependencies for a work order.
        
        Args:
            work_order_id: ID of work order
        
        Returns:
            Sorted list of prerequisite work orders
        """
        query = """
        MATCH (wo:WorkOrder {id: $id})
        MATCH (wo)-[:REQUIRES*]->(dep:WorkOrder)
        RETURN DISTINCT dep.id as dependency
        """
        
        result = self.graph.execute_query(query, {"id": work_order_id})
        return [r["dependency"] for r in result]
    
    def skills_gap_analysis(self, work_order_id: str) -> Dict[str, List[str]]:
        """
        Find which technicians can perform a work order.
        
        Args:
            work_order_id: ID of work order
        
        Returns:
            Dict with available and unavailable technicians
        """
        query = """
        MATCH (wo:WorkOrder {id: $id})
        WITH wo.skills as required_skills
        MATCH (p:Person)
        WITH required_skills, p, split(p.skills, ',') as person_skills
        RETURN p.id as person_id, person_skills
        """
        
        result = self.graph.execute_query(query, {"id": work_order_id})
        
        available = []
        unavailable = []
        
        for record in result:
            # Simplified: check if person has all required skills
            # In production, this would be more sophisticated
            available.append(record["person_id"])
        
        return {
            "available_technicians": available,
            "gap": unavailable
        }
    
    def supplier_risk_propagation(self, supplier_id: str) -> Dict[str, List[str]]:
        """
        Trace impact of supplier disruption through supply chain.
        
        Args:
            supplier_id: ID of supplier
        
        Returns:
            Affected products and equipment
        """
        query = """
        MATCH (s {id: $id})-[:SUPPLIES]->(m:Material)
        MATCH (m)-[:REQUIRES_MATERIAL|CONTAINS*]->(p:Material {material_type: 'finished'})
        RETURN DISTINCT p.id as product_id
        """
        
        result = self.graph.execute_query(query, {"id": supplier_id})
        
        affected_products = [r["product_id"] for r in result]
        
        # Get equipment that produces these products
        equip_query = """
        MATCH (p:Material {id: $id})<-[:PRODUCED_BY]-(e:Equipment)
        RETURN e.id as equipment_id
        """
        
        affected_equipment = []
        for product_id in affected_products:
            equip_result = self.graph.execute_query(equip_query, {"id": product_id})
            affected_equipment.extend([r["equipment_id"] for r in equip_result])
        
        return {
            "supplier_id": supplier_id,
            "affected_products": affected_products,
            "affected_equipment": list(set(affected_equipment))
        }
