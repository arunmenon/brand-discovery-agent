import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create mock classes for crewai
class MockCrew:
    def __init__(self, agents, tasks, process, verbose):
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.verbose = verbose

class MockProcess:
    sequential = "sequential"

# Mock the crewai module
sys.modules['crewai'] = MagicMock()
sys.modules['crewai'].Crew = MockCrew
sys.modules['crewai'].Process = MockProcess
sys.modules['crewai.project'] = MagicMock()
sys.modules['crewai.project'].CrewBase = lambda x: x
sys.modules['crewai.project'].before_kickoff = lambda x: x
sys.modules['crewai.project'].after_kickoff = lambda x: x
sys.modules['crewai.project'].crew = lambda x: x

# Now we can import the modules that depend on crewai
from core.crew_definition import BrandGraphCrew
from core.BrandGraphIngester import BrandGraphIngester

# Mock the task functions from core.tasks
@patch('core.tasks.brand_discovery_task')
@patch('core.tasks.attribute_extraction_task')
@patch('core.tasks.variation_generation_task')
def test_crew_brand_mode(mock_var_task, mock_attr_task, mock_brand_task):
    """
    Test that when input mode is "brand", the crew is built with the attribute extraction 
    and variation generation tasks.
    """
    # Set up our mocks
    mock_attr_task_obj = MagicMock()
    mock_attr_task_obj.description = 'For the brand "{brand}" and product type "{product_type}", extract attributes.'
    mock_attr_task.return_value = mock_attr_task_obj
    
    mock_var_task_obj = MagicMock()
    mock_var_task_obj.description = 'For the brand "{brand}", generate variations.'
    mock_var_task.return_value = mock_var_task_obj
    
    # Create and test the crew
    crew_instance = BrandGraphCrew()
    input_data = {
        "mode": "brand",
        "brand": "TestBrand",
        "category": "TestCategory",
        "product_type": "TestProduct"
    }
    crew_instance.capture_inputs(input_data)
    crew_obj = crew_instance.crew()
    
    # In brand mode, expect exactly two tasks
    assert len(crew_obj.tasks) == 2, "Expected 2 tasks in brand mode"
    print("PASS: test_crew_brand_mode - Expected 2 tasks in brand mode")

@patch('core.BrandGraphIngester.BrandGraphIngester.upsert_brand_info')
def test_update_graph_brand_mode(mock_upsert):
    """
    Test that update_graph correctly parses outputs for brand mode and calls upsert.
    """
    crew_instance = BrandGraphCrew()
    input_data = {
        "mode": "brand",
        "brand": "TestBrand",
        "category": "TestCategory",
        "product_type": "TestProduct"
    }
    crew_instance.capture_inputs(input_data)
    
    # Simulate task outputs
    output = {
        "attribute_extraction_task": '{"Color": ["Red", "Blue"], "Size": ["8", "9"]}',
        "variation_generation_task": '["TestBrandX", "T3stBrand"]'
    }
    
    crew_instance.update_graph(output)
    mock_upsert.assert_called_once()
    print("PASS: test_update_graph_brand_mode - upsert_brand_info called once")

if __name__ == "__main__":
    # Run our mocked tests
    test_crew_brand_mode()
    test_update_graph_brand_mode()
    print("All tests passed!")