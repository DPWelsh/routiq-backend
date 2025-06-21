"""
Enhanced Patient Visibility Test Suite
Tests the new appointment type, next appointment time, and treatment notes features
"""

import pytest
import requests
from datetime import datetime
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"
TEST_ORGANIZATION_ID = "surfrehab"
TIMEOUT = 30

class TestEnhancedPatientFeatures:
    """Test suite for enhanced patient information features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    def test_enhanced_patient_list_has_new_fields(self):
        """Test that patient list includes new enhanced fields"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["patients"]:
            patient = data["patients"][0]
            
            # Check for enhanced fields
            enhanced_fields = [
                "next_appointment_time", 
                "next_appointment_type", 
                "primary_appointment_type", 
                "treatment_notes",
                "hours_until_next_appointment"
            ]
            
            for field in enhanced_fields:
                assert field in patient, f"Missing enhanced field: {field}"
    
    def test_new_enhanced_endpoint_works(self):
        """Test new enhanced endpoint with appointment details"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active/with-appointments",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "organization_id" in data
        assert "patients" in data
        assert "total_count" in data
        
        if data["patients"]:
            patient = data["patients"][0]
            assert "priority" in patient
            assert "next_appointment_type" in patient
            assert "treatment_notes" in patient
    
    def test_appointment_type_filtering(self):
        """Test filtering patients by appointment type"""
        # Get available appointment types first
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/appointment-types/summary",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "appointment_types" in data
        assert "total_types" in data
        
        # If there are appointment types, test filtering
        if data["appointment_types"]:
            type_info = data["appointment_types"][0]
            type_name = type_info.get("next_appointment_type") or type_info.get("primary_appointment_type")
            
            if type_name:
                filter_response = requests.get(
                    f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/by-appointment-type/{type_name}",
                    headers=self.headers,
                    timeout=TIMEOUT
                )
                
                assert filter_response.status_code == 200
                filter_data = filter_response.json()
                assert "appointment_type" in filter_data
                assert filter_data["appointment_type"] == type_name 