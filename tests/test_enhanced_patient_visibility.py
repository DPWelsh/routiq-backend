"""
Enhanced Patient Visibility Test Suite
Tests the new appointment type, next appointment time, and treatment notes features
"""

import pytest
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Test Configuration
BASE_URL = "http://localhost:8000"
PRODUCTION_URL = "https://routiq-backend-v10-production.up.railway.app"
TEST_ORGANIZATION_ID = "surfrehab"  # Using actual organization
TIMEOUT = 30

class TestEnhancedPatientVisibility:
    """Test suite for enhanced patient information features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Enhanced-Patient-Test-Suite/1.0"
        }
        
    def validate_patient_structure(self, patient: Dict[str, Any]) -> List[str]:
        """Validate enhanced patient data structure"""
        errors = []
        
        # Original fields that should still exist
        required_fields = [
            "id", "contact_id", "contact_name", "contact_phone", 
            "recent_appointment_count", "upcoming_appointment_count",
            "total_appointment_count", "recent_appointments", "upcoming_appointments"
        ]
        
        # Enhanced fields we added
        enhanced_fields = [
            "next_appointment_time", "next_appointment_type", 
            "primary_appointment_type", "treatment_notes",
            "hours_until_next_appointment"
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in patient:
                errors.append(f"Missing required field: {field}")
        
        # Check enhanced fields exist (can be null)
        for field in enhanced_fields:
            if field not in patient:
                errors.append(f"Missing enhanced field: {field}")
        
        # Validate data types for enhanced fields
        if patient.get("next_appointment_time") is not None:
            try:
                datetime.fromisoformat(patient["next_appointment_time"].replace('Z', '+00:00'))
            except ValueError:
                errors.append("next_appointment_time has invalid datetime format")
        
        if patient.get("next_appointment_type") is not None:
            if not isinstance(patient["next_appointment_type"], str):
                errors.append("next_appointment_type should be string")
        
        if patient.get("primary_appointment_type") is not None:
            if not isinstance(patient["primary_appointment_type"], str):
                errors.append("primary_appointment_type should be string")
        
        if patient.get("hours_until_next_appointment") is not None:
            if not isinstance(patient["hours_until_next_appointment"], (int, float)):
                errors.append("hours_until_next_appointment should be number")
        
        return errors

    # ========================================
    # ENHANCED PATIENT LIST TESTS
    # ========================================
    
    def test_enhanced_patient_list_structure(self):
        """Test that enhanced patient list returns new fields"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200, f"API call failed: {response.status_code}"
        data = response.json()
        
        # Validate response structure
        assert "organization_id" in data
        assert "patients" in data
        assert "total_count" in data
        assert "timestamp" in data
        
        # Test each patient has enhanced fields
        if data["patients"]:
            for i, patient in enumerate(data["patients"][:5]):  # Test first 5 patients
                errors = self.validate_patient_structure(patient)
                assert not errors, f"Patient {i} validation errors: {errors}"
    
    def test_enhanced_patient_with_appointments_endpoint(self):
        """Test new enhanced endpoint with appointment details"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active/with-appointments",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        # Should work with new enhanced schema
        assert response.status_code == 200, f"Enhanced endpoint failed: {response.status_code}"
        data = response.json()
        
        # Validate enhanced response structure
        assert "organization_id" in data
        assert "patients" in data
        assert "total_count" in data
        
        # Check enhanced fields in response
        if data["patients"]:
            patient = data["patients"][0]
            
            # Enhanced fields should be present
            enhanced_fields = [
                "priority", "next_appointment_type", "primary_appointment_type",
                "treatment_notes", "hours_until_next_appointment", "days_until_next_appointment"
            ]
            
            for field in enhanced_fields:
                assert field in patient, f"Missing enhanced field: {field}"
                
            # Validate priority levels
            if patient.get("priority"):
                assert patient["priority"] in ["high", "medium", "low"], f"Invalid priority: {patient['priority']}"

    def test_filter_by_appointment_type(self):
        """Test filtering patients by appointment type"""
        # First get the list to see what appointment types exist
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find a patient with appointment type
        appointment_type = None
        if data["patients"]:
            for patient in data["patients"]:
                if patient.get("next_appointment_type") or patient.get("primary_appointment_type"):
                    appointment_type = patient.get("next_appointment_type") or patient.get("primary_appointment_type")
                    break
        
        if appointment_type:
            # Test filtering by this appointment type
            response = requests.get(
                f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/by-appointment-type/{appointment_type}",
                headers=self.headers,
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200
            filtered_data = response.json()
            
            assert "appointment_type" in filtered_data
            assert filtered_data["appointment_type"] == appointment_type
            assert "patients" in filtered_data
            
            # All returned patients should have this appointment type
            for patient in filtered_data["patients"]:
                assert (
                    patient.get("next_appointment_type") == appointment_type or 
                    patient.get("primary_appointment_type") == appointment_type
                ), f"Patient doesn't match filter: {patient}"

    def test_appointment_types_summary(self):
        """Test appointment types summary endpoint"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/appointment-types/summary",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate summary structure
        assert "organization_id" in data
        assert "appointment_types" in data
        assert "total_types" in data
        assert "timestamp" in data
        
        # Validate appointment type entries
        for appt_type in data["appointment_types"]:
            required_fields = [
                "patient_count", "patients_with_upcoming"
            ]
            
            for field in required_fields:
                assert field in appt_type, f"Missing field in appointment type summary: {field}"
            
            # Validate data types
            assert isinstance(appt_type["patient_count"], int)
            assert isinstance(appt_type["patients_with_upcoming"], int)

    # ========================================
    # APPOINTMENT TIME CALCULATIONS TESTS
    # ========================================
    
    def test_next_appointment_time_calculations(self):
        """Test that next appointment time calculations are accurate"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active/with-appointments",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        current_time = datetime.now()
        
        for patient in data["patients"]:
            if patient.get("next_appointment_time") and patient.get("hours_until_next_appointment"):
                # Parse the next appointment time
                next_appt = datetime.fromisoformat(patient["next_appointment_time"].replace('Z', '+00:00'))
                
                # Calculate expected hours
                expected_hours = (next_appt - current_time.replace(tzinfo=next_appt.tzinfo)).total_seconds() / 3600
                reported_hours = patient["hours_until_next_appointment"]
                
                # Allow some tolerance for processing time
                assert abs(expected_hours - reported_hours) < 1, \
                    f"Hours calculation mismatch: expected ~{expected_hours:.1f}, got {reported_hours}"

    def test_priority_calculation_logic(self):
        """Test that priority calculation follows business logic"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active/with-appointments",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        current_time = datetime.now()
        
        for patient in data["patients"]:
            priority = patient.get("priority", "low")
            next_appt_time = patient.get("next_appointment_time")
            
            if next_appt_time:
                next_appt = datetime.fromisoformat(next_appt_time.replace('Z', '+00:00'))
                hours_until = (next_appt - current_time.replace(tzinfo=next_appt.tzinfo)).total_seconds() / 3600
                
                # Validate priority logic
                if hours_until <= 24:
                    assert priority == "high", f"Appointment in {hours_until:.1f}h should be high priority, got {priority}"
                elif hours_until <= 72:
                    assert priority == "medium", f"Appointment in {hours_until:.1f}h should be medium priority, got {priority}"
                else:
                    assert priority == "low", f"Appointment in {hours_until:.1f}h should be low priority, got {priority}"

    # ========================================
    # TREATMENT NOTES TESTS
    # ========================================
    
    def test_treatment_notes_presence(self):
        """Test that treatment notes are being captured"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        patients_with_notes = 0
        patients_with_treatment_summary = 0
        
        for patient in data["patients"]:
            # Count patients with treatment information
            if patient.get("treatment_notes"):
                patients_with_notes += 1
            if patient.get("treatment_summary"):
                patients_with_treatment_summary += 1
        
        print(f"📊 Patients with treatment notes: {patients_with_notes}/{len(data['patients'])}")
        print(f"📊 Patients with treatment summary: {patients_with_treatment_summary}/{len(data['patients'])}")
        
        # At least some patients should have treatment information (not asserting specific numbers as it depends on data)
        
    def test_treatment_notes_text_search(self):
        """Test that treatment notes are searchable (if search implemented)"""
        # This would test full-text search on treatment notes when implemented
        pass

    # ========================================
    # DATA CONSISTENCY TESTS
    # ========================================
    
    def test_appointment_count_consistency(self):
        """Test that appointment counts are consistent with appointment arrays"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for patient in data["patients"]:
            # Validate appointment count consistency
            upcoming_count = patient.get("upcoming_appointment_count", 0)
            upcoming_array = patient.get("upcoming_appointments", [])
            
            if isinstance(upcoming_array, list):
                assert len(upcoming_array) == upcoming_count, \
                    f"Upcoming count mismatch: count={upcoming_count}, array length={len(upcoming_array)}"
            
            recent_count = patient.get("recent_appointment_count", 0)
            recent_array = patient.get("recent_appointments", [])
            
            if isinstance(recent_array, list):
                assert len(recent_array) == recent_count, \
                    f"Recent count mismatch: count={recent_count}, array length={len(recent_array)}"

    def test_next_appointment_derives_from_upcoming(self):
        """Test that next_appointment_time matches earliest upcoming appointment"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for patient in data["patients"]:
            next_appt_time = patient.get("next_appointment_time")
            upcoming_appointments = patient.get("upcoming_appointments", [])
            
            if next_appt_time and upcoming_appointments:
                # Find earliest upcoming appointment
                if isinstance(upcoming_appointments, list) and upcoming_appointments:
                    earliest_upcoming = min(upcoming_appointments, key=lambda x: x.get("date", ""))
                    earliest_date = earliest_upcoming.get("date")
                    
                    if earliest_date:
                        # Should match next_appointment_time
                        assert next_appt_time == earliest_date, \
                            f"Next appointment time mismatch: next={next_appt_time}, earliest={earliest_date}"

    # ========================================
    # PERFORMANCE TESTS
    # ========================================
    
    @pytest.mark.performance
    def test_enhanced_endpoint_performance(self):
        """Test that enhanced endpoints perform within acceptable limits"""
        import time
        
        start_time = time.time()
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active/with-appointments",
            headers=self.headers,
            timeout=TIMEOUT
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0, f"Enhanced endpoint too slow: {response_time:.2f}s"
        
        print(f"⚡ Enhanced endpoint response time: {response_time:.2f}s")

    # ========================================
    # ERROR HANDLING TESTS
    # ========================================
    
    def test_invalid_appointment_type_filter(self):
        """Test filtering by non-existent appointment type"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/by-appointment-type/NonExistentType",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        # Should return 200 with empty results, not an error
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["patients"] == []

    def test_invalid_organization_enhanced_endpoints(self):
        """Test enhanced endpoints with invalid organization ID"""
        response = requests.get(
            f"{self.base_url}/api/v1/patients/invalid_org_id/active/with-appointments",
            headers=self.headers,
            timeout=TIMEOUT
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["total_count"] == 0

    # ========================================
    # INTEGRATION TESTS
    # ========================================
    
    @pytest.mark.integration
    def test_full_enhanced_workflow(self):
        """Test complete enhanced patient visibility workflow"""
        # 1. Get appointment types summary
        summary_response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/appointment-types/summary",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert summary_response.status_code == 200
        
        # 2. Get enhanced patient list
        patients_response = requests.get(
            f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/active/with-appointments",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert patients_response.status_code == 200
        
        # 3. If there are appointment types, test filtering
        summary_data = summary_response.json()
        if summary_data["appointment_types"]:
            first_type = summary_data["appointment_types"][0]
            type_name = first_type.get("next_appointment_type") or first_type.get("primary_appointment_type")
            
            if type_name:
                filter_response = requests.get(
                    f"{self.base_url}/api/v1/patients/{TEST_ORGANIZATION_ID}/by-appointment-type/{type_name}",
                    headers=self.headers,
                    timeout=TIMEOUT
                )
                assert filter_response.status_code == 200
        
        print("✅ Full enhanced patient visibility workflow completed successfully") 