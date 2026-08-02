#!/usr/bin/env python3
# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Tests for lead capture bot."""
import json
import sys
import tempfile
from pathlib import Path

# Add bots to path
sys.path.insert(0, str(Path(__file__).parent.parent / "bots"))

from lead_capture_bot import (
    classify_lead,
    normalize_lead,
    LeadClassification,
)


def test_classify_jobseeker():
    """Test jobseeker classification."""
    classification = classify_lead(
        intent="Looking for opportunity",
        message="I'm interested in working at ClearGlass",
    )
    assert classification.type == "jobseeker"
    assert classification.confidence > 0.3


def test_classify_recruiter():
    """Test recruiter classification."""
    classification = classify_lead(
        message="We are recruiting for your team, do you want to hire?",
        email="recruiter@recruiter.com",
    )
    assert classification.type == "recruiter"
    assert classification.confidence > 0.2


def test_classify_employer():
    """Test employer classification."""
    classification = classify_lead(
        intent="Looking for security consulting services",
        message="We need an enterprise IT security solution",
    )
    assert classification.type == "employer"
    assert classification.confidence > 0.2


def test_classify_vendor():
    """Test vendor classification."""
    classification = classify_lead(
        message="We'd like to partner on a reseller basis.",
    )
    assert classification.type == "vendor"


def test_classify_press():
    """Test press classification."""
    classification = classify_lead(
        message="I'm a journalist writing about AI automation",
    )
    assert classification.type == "press"


def test_normalize_lead():
    """Test lead normalization."""
    lead = normalize_lead(
        name="John Doe",
        email="john@example.com",
        company="Acme Corp",
        message="Interested in your services",
        intent="Enterprise audit",
    )
    assert lead is not None
    assert lead.email == "john@example.com"
    assert lead.first_name == "John"
    assert lead.last_name == "Doe"
    assert lead.company == "Acme Corp"


def test_normalize_lead_invalid_email():
    """Test that leads without valid email are rejected."""
    lead = normalize_lead(
        name="John Doe",
        email="invalid",
        message="Test",
    )
    assert lead is None


def test_normalize_lead_single_name():
    """Test lead normalization with single name."""
    lead = normalize_lead(
        name="Madonna",
        email="madonna@example.com",
    )
    assert lead is not None
    assert lead.first_name == "Madonna"
    assert lead.last_name == ""


def test_classification_serialization():
    """Test that classification can be serialized to JSON."""
    classification = classify_lead(
        message="Looking for job opportunities"
    )
    data = {
        "type": classification.type,
        "confidence": classification.confidence,
        "reason": classification.reason,
    }
    json_str = json.dumps(data)
    assert isinstance(json.loads(json_str), dict)


def test_normalize_lead_all_fields():
    """Test lead with all fields populated."""
    lead = normalize_lead(
        name="Jane Smith",
        email="jane@company.com",
        company="Big Corp",
        job_title="CISO",
        phone="555-1234",
        message="Please call me",
        intent="Security assessment",
        source="formsubmit",
        source_url="https://example.com/contact",
        form_submission_id="fs-12345",
        metadata={"utm_source": "google", "utm_campaign": "q3-campaign"},
    )
    assert lead is not None
    assert lead.job_title == "CISO"
    assert lead.phone == "555-1234"
    assert lead.metadata["utm_source"] == "google"


if __name__ == "__main__":
    test_classify_jobseeker()
    test_classify_recruiter()
    test_classify_employer()
    test_classify_vendor()
    test_classify_press()
    test_normalize_lead()
    test_normalize_lead_invalid_email()
    test_normalize_lead_single_name()
    test_classification_serialization()
    test_normalize_lead_all_fields()
    print("All tests passed!")
