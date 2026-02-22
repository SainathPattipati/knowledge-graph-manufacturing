"""
Manufacturing graph ontology schema definition.

Defines node types, relationship types, and constraints for the knowledge graph.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class NodeType(str, Enum):
    """Node types in manufacturing graph."""
    EQUIPMENT = "Equipment"
    COMPONENT = "Component"
    MATERIAL = "Material"
    PROCESS = "Process"
    FAILURE = "Failure"
    WORK_ORDER = "WorkOrder"
    SENSOR = "Sensor"
    PERSON = "Person"
    LOCATION = "Location"


class RelationType(str, Enum):
    """Relationship types in manufacturing graph."""
    HAS_COMPONENT = "HAS_COMPONENT"
    PART_OF = "PART_OF"
    CONNECTED_TO = "CONNECTED_TO"
    CAUSES_FAILURE = "CAUSES_FAILURE"
    REQUIRES_MATERIAL = "REQUIRES_MATERIAL"
    PERFORMED_BY = "PERFORMED_BY"
    LOCATED_AT = "LOCATED_AT"
    MONITORS = "MONITORS"
    CONTAINS = "CONTAINS"
    TRIGGERS = "TRIGGERS"
    PRODUCED_BY = "PRODUCED_BY"


@dataclass
class PropertySchema:
    """Schema for node/relationship properties."""
    name: str
    data_type: str  # "string", "integer", "float", "datetime", "boolean"
    required: bool = False
    description: str = ""


class ManufacturingSchema:
    """Complete manufacturing graph schema."""
    
    # Node property schemas
    NODE_SCHEMAS: Dict[NodeType, List[PropertySchema]] = {
        NodeType.EQUIPMENT: [
            PropertySchema("equipment_id", "string", required=True),
            PropertySchema("equipment_type", "string", required=True),  # pump, motor, etc.
            PropertySchema("manufacturer", "string"),
            PropertySchema("model", "string"),
            PropertySchema("serial_number", "string"),
            PropertySchema("installation_date", "datetime"),
            PropertySchema("operational_status", "string"),  # "operational", "degraded", "down"
            PropertySchema("mtbf_hours", "float"),  # Mean Time Between Failures
            PropertySchema("age_hours", "float"),
            PropertySchema("last_maintenance", "datetime"),
        ],
        NodeType.COMPONENT: [
            PropertySchema("component_id", "string", required=True),
            PropertySchema("component_type", "string", required=True),
            PropertySchema("supplier", "string"),
            PropertySchema("part_number", "string"),
            PropertySchema("quantity_on_hand", "integer"),
            PropertySchema("cost", "float"),
            PropertySchema("lead_time_days", "integer"),
        ],
        NodeType.MATERIAL: [
            PropertySchema("material_id", "string", required=True),
            PropertySchema("material_name", "string", required=True),
            PropertySchema("material_type", "string"),  # "raw", "wip", "finished"
            PropertySchema("batch_number", "string"),
            PropertySchema("quantity", "float"),
            PropertySchema("unit", "string"),  # kg, liters, units
            PropertySchema("supplier", "string"),
            PropertySchema("received_date", "datetime"),
            PropertySchema("expiration_date", "datetime"),
        ],
        NodeType.PROCESS: [
            PropertySchema("process_id", "string", required=True),
            PropertySchema("process_name", "string", required=True),
            PropertySchema("process_type", "string"),
            PropertySchema("cycle_time_seconds", "float"),
            PropertySchema("standard_cost", "float"),
        ],
        NodeType.FAILURE: [
            PropertySchema("failure_id", "string", required=True),
            PropertySchema("failure_mode", "string", required=True),
            PropertySchema("severity", "string"),  # "low", "medium", "high", "critical"
            PropertySchema("frequency", "string"),  # "rare", "occasional", "frequent"
            PropertySchema("first_occurrence", "datetime"),
            PropertySchema("last_occurrence", "datetime"),
            PropertySchema("occurrence_count", "integer"),
        ],
        NodeType.WORK_ORDER: [
            PropertySchema("work_order_id", "string", required=True),
            PropertySchema("work_type", "string"),  # "preventive", "corrective", "predictive"
            PropertySchema("status", "string"),  # "open", "in_progress", "completed"
            PropertySchema("created_date", "datetime"),
            PropertySchema("due_date", "datetime"),
            PropertySchema("completed_date", "datetime"),
            PropertySchema("estimated_hours", "float"),
            PropertySchema("actual_hours", "float"),
        ],
        NodeType.SENSOR: [
            PropertySchema("sensor_id", "string", required=True),
            PropertySchema("sensor_type", "string"),  # "temperature", "vibration", "pressure"
            PropertySchema("measurement_unit", "string"),
            PropertySchema("sampling_frequency_hz", "float"),
            PropertySchema("last_reading", "float"),
            PropertySchema("last_reading_timestamp", "datetime"),
        ],
        NodeType.PERSON: [
            PropertySchema("person_id", "string", required=True),
            PropertySchema("name", "string"),
            PropertySchema("role", "string"),  # "operator", "technician", "engineer"
            PropertySchema("skills", "string"),  # comma-separated
            PropertySchema("certifications", "string"),
        ],
        NodeType.LOCATION: [
            PropertySchema("location_id", "string", required=True),
            PropertySchema("location_name", "string", required=True),
            PropertySchema("location_type", "string"),  # "line", "warehouse", "facility"
        ],
    }
    
    # Relationship property schemas
    RELATIONSHIP_SCHEMAS: Dict[RelationType, List[PropertySchema]] = {
        RelationType.HAS_COMPONENT: [
            PropertySchema("quantity", "integer"),
            PropertySchema("part_number", "string"),
        ],
        RelationType.CONNECTED_TO: [
            PropertySchema("connection_type", "string"),  # "fluid", "electrical", "mechanical"
            PropertySchema("flow_rate", "float"),
        ],
        RelationType.CAUSES_FAILURE: [
            PropertySchema("causality_probability", "float"),  # 0.0-1.0
            PropertySchema("lag_hours", "integer"),
        ],
        RelationType.MONITORS: [
            PropertySchema("alert_threshold", "float"),
            PropertySchema("alert_type", "string"),  # "high", "low", "range"
        ],
        RelationType.PERFORMED_BY: [
            PropertySchema("effort_hours", "float"),
            PropertySchema("completion_date", "datetime"),
        ],
    }
    
    @classmethod
    def validate_node(cls, node_type: NodeType, properties: Dict[str, Any]) -> bool:
        """Validate node properties against schema."""
        schema = cls.NODE_SCHEMAS.get(node_type, [])
        
        # Check required properties
        for prop_schema in schema:
            if prop_schema.required and prop_schema.name not in properties:
                raise ValueError(f"Missing required property: {prop_schema.name}")
        
        return True
    
    @classmethod
    def validate_relationship(
        cls,
        rel_type: RelationType,
        properties: Dict[str, Any]
    ) -> bool:
        """Validate relationship properties against schema."""
        schema = cls.RELATIONSHIP_SCHEMAS.get(rel_type, [])
        
        for prop_schema in schema:
            if prop_schema.required and prop_schema.name not in properties:
                raise ValueError(f"Missing required property: {prop_schema.name}")
        
        return True


# Graph constraints
GRAPH_CONSTRAINTS = {
    "equipment_unique_id": "EQUIPMENT must have unique equipment_id",
    "component_unique_id": "COMPONENT must have unique component_id",
    "material_unique_id": "MATERIAL must have unique material_id",
    "no_circular_contains": "CONTAINS relationships must form DAG (no cycles)",
    "work_order_performer": "PERFORMED_BY must reference valid PERSON",
}
