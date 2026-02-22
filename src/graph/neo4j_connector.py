"""Neo4j database connector with connection pooling and query optimization."""

from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from neo4j import GraphDatabase, Session, Driver


class Neo4jConnector:
    """High-level Neo4j interface for manufacturing graph."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        auth: tuple[str, str] = ("neo4j", "password"),
        max_pool_size: int = 50
    ):
        """
        Initialize Neo4j connector.
        
        Args:
            uri: Neo4j server URI
            auth: (username, password) tuple
            max_pool_size: Connection pool size
        """
        self.uri = uri
        self.auth = auth
        self.driver: Driver | None = None
        self.max_pool_size = max_pool_size
        
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to Neo4j."""
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=self.auth,
            max_connection_pool_size=self.max_pool_size
        )
    
    @contextmanager
    def session(self):
        """Context manager for Neo4j sessions."""
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def create_indexes(self) -> None:
        """Create performance indexes on key properties."""
        with self.session() as session:
            # Equipment indexes
            session.run(
                "CREATE INDEX equipment_id IF NOT EXISTS FOR (e:Equipment) ON (e.equipment_id)"
            )
            session.run(
                "CREATE INDEX equipment_type IF NOT EXISTS FOR (e:Equipment) ON (e.equipment_type)"
            )
            
            # Component indexes
            session.run(
                "CREATE INDEX component_id IF NOT EXISTS FOR (c:Component) ON (c.component_id)"
            )
            
            # Material indexes
            session.run(
                "CREATE INDEX material_id IF NOT EXISTS FOR (m:Material) ON (m.material_id)"
            )
            session.run(
                "CREATE INDEX batch_number IF NOT EXISTS FOR (m:Material) ON (m.batch_number)"
            )
            
            # Failure indexes
            session.run(
                "CREATE INDEX failure_mode IF NOT EXISTS FOR (f:Failure) ON (f.failure_mode)"
            )
    
    def execute_query(
        self,
        query: str,
        parameters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
        
        Returns:
            List of result dictionaries
        """
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def create_node(
        self,
        label: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a node in the graph."""
        props_str = ", ".join(f"{k}: ${k}" for k in properties.keys())
        query = f"CREATE (n:{label} {{{props_str}}}) RETURN n"
        
        result = self.execute_query(query, properties)
        return result[0] if result else {}
    
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        source_label: str,
        target_label: str,
        rel_type: str,
        id_property: str = "id",
        properties: Dict[str, Any] | None = None
    ) -> bool:
        """Create a relationship between two nodes."""
        props = properties or {}
        props_str = ", ".join(f"{k}: ${k}" for k in props.keys()) if props else ""
        
        if props_str:
            props_str = f" {{{props_str}}}"
        
        query = f"""
        MATCH (source:{source_label} {{{id_property}: $source_id}})
        MATCH (target:{target_label} {{{id_property}: $target_id}})
        CREATE (source)-[r:{rel_type}{props_str}]->(target)
        RETURN r
        """
        
        params = {"source_id": source_id, "target_id": target_id}
        params.update(props)
        
        result = self.execute_query(query, params)
        return bool(result)
    
    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 10
    ) -> List[str]:
        """Find shortest path between two nodes."""
        query = f"""
        MATCH (source {{id: $source_id}}), (target {{id: $target_id}})
        MATCH path = shortestPath((source)-[*..{max_hops}]->(target))
        RETURN [n in nodes(path) | n.id] as path
        """
        
        result = self.execute_query(query, {
            "source_id": source_id,
            "target_id": target_id
        })
        
        return result[0]["path"] if result else []
    
    def get_neighbors(
        self,
        node_id: str,
        relationship_type: str | None = None,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """Get neighboring nodes within specified depth."""
        rel_filter = f":{relationship_type}" if relationship_type else ""
        query = f"""
        MATCH (n {{id: $id}})-[{rel_filter}*1..{depth}]->(neighbor)
        RETURN DISTINCT neighbor
        """
        
        return self.execute_query(query, {"id": node_id})
    
    def close(self) -> None:
        """Close database connection."""
        if self.driver:
            self.driver.close()
