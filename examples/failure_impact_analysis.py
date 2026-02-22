"""Example: Analyze equipment failure impact through the graph."""

from src.graph.neo4j_connector import Neo4jConnector
from src.reasoning.failure_propagator import FailurePropagator


def example_failure_impact():
    """Demonstrate failure impact analysis."""
    
    # Connect to Neo4j
    graph = Neo4jConnector()
    propagator = FailurePropagator(graph)
    
    # Analyze failure of critical pump
    impact = propagator.analyze_failure("pump_103", max_depth=5)
    
    print("=== FAILURE IMPACT ANALYSIS ===")
    print(f"Failed equipment: {impact.initial_equipment}")
    print(f"Directly affected: {len(impact.directly_affected)} components")
    print(f"Cascade affected: {len(impact.cascade_affected)} components")
    print(f"Total affected: {impact.total_affected}")
    print(f"\nCritical path: {' -> '.join(impact.critical_path)}")
    print(f"\nAffected products: {impact.affected_products}")
    print(f"Estimated downtime: {impact.estimated_downtime_hours:.1f} hours")
    
    graph.close()


if __name__ == "__main__":
    example_failure_impact()
