import json
import pytest
from unittest.mock import patch, MagicMock
from core.crew_definition import BrandGraphCrew
from core.graph_updater import BrandGraphIngester

def test_crew_brand_mode():
    """
    Test that when input mode is "brand", the crew is built with the attribute extraction 
    and variation generation tasks.
    """
    crew_instance = BrandGraphCrew()
    input_data = {
        "mode": "brand",
        "brand": "TestBrand",
        "category": "TestCategory",
        "product_type": "TestProduct"
    }
    crew_instance.capture_inputs(input_data)
    crew_obj = crew_instance.crew()
    
    # In brand mode, expect exactly two tasks.
    assert len(crew_obj.tasks) == 2, "Expected 2 tasks in brand mode"
    
    # Check that the task descriptions include the '{brand}' placeholder.
    attr_desc = crew_obj.tasks[0].description
    var_desc = crew_obj.tasks[1].description
    assert "{brand}" in attr_desc
    assert "{brand}" in var_desc

@patch('core.graph_updater.BrandGraphIngester.upsert_brand_info')
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
    
    # Simulate task outputs.
    output = {
        "attribute_extraction_task": '{"Color": ["Red", "Blue"], "Size": ["8", "9"]}',
        "variation_generation_task": '["TestBrandX", "T3stBrand"]'
    }
    
    crew_instance.update_graph(output)
    mock_upsert.assert_called_once_with(
        "TestBrand",
        "TestCategory",
        "TestProduct",
        {"Color": ["Red", "Blue"], "Size": ["8", "9"]},
        ["TestBrandX", "T3stBrand"]
    )

@patch('core.graph_updater.BrandGraphIngester.upsert_brand_info')
def test_update_graph_category_mode(mock_upsert):
    """
    Test that in category mode, update_graph iterates over discovered brands and calls upsert for each.
    """
    crew_instance = BrandGraphCrew()
    input_data = {
        "mode": "category",
        "category": "TestCategory",
        "product_type": "TestProduct"
    }
    crew_instance.capture_inputs(input_data)
    
    # Simulate output from the brand discovery task.
    discovered_brands = ["BrandA", "BrandB"]
    output = {
        "brand_discovery_task": json.dumps(discovered_brands)
    }
    
    # Patch the attribute extraction and variation generation task invocations.
    with patch.object(crew_instance, 'attribute_extraction_task') as mock_attr_task:
        fake_attr_task = MagicMock()
        fake_attr_task.description = 'For the brand "{brand}" and product type "{product_type}", extract attributes.'
        fake_attr_task.agent.invoke.return_value = '{"Color": ["Red"], "Size": ["8"]}'
        mock_attr_task.return_value = fake_attr_task

        with patch.object(crew_instance, 'variation_generation_task') as mock_var_task:
            fake_var_task = MagicMock()
            fake_var_task.description = 'For the brand "{brand}", generate variations.'
            fake_var_task.agent.invoke.return_value = '["BrandA_Var1"]'
            mock_var_task.return_value = fake_var_task

            crew_instance.update_graph(output)
            # Expect upsert to be called for each discovered brand (2 brands).
            assert mock_upsert.call_count == 2
