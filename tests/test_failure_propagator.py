"""Unit tests for failure propagator."""

import pytest
from unittest.mock import Mock, MagicMock
from src.reasoning.failure_propagator import FailurePropagator


class TestFailurePropagator:
    """Test suite for FailurePropagator."""
    
    @pytest.fixture
    def mock_graph(self):
        """Create mock graph connector."""
        mock = Mock()
        mock.execute_query = MagicMock(return_value=[])
        return mock
    
    @pytest.fixture
    def propagator(self, mock_graph):
        """Create propagator with mock graph."""
        return FailurePropagator(mock_graph)
    
    def test_analyze_failure_returns_impact(self, propagator, mock_graph):
        """Test that analyze_failure returns FailureImpact."""
        mock_graph.execute_query.return_value = []
        
        impact = propagator.analyze_failure("pump_123")
        
        assert impact.initial_equipment == "pump_123"
        assert impact.total_affected >= 1
    
    def test_get_affected_products(self, propagator, mock_graph):
        """Test product impact calculation."""
        mock_graph.execute_query.return_value = [
            {"product_id": "product_A"},
            {"product_id": "product_B"}
        ]
        
        products = propagator._get_affected_products({"equip_1", "equip_2"})
        
        assert len(products) == 2
        assert "product_A" in products
    
    def test_estimate_downtime(self, propagator, mock_graph):
        """Test downtime estimation."""
        mock_graph.execute_query.return_value = [{"mtbf": 1000}]
        
        downtime = propagator._estimate_downtime({"equip_1"})
        
        assert downtime > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
