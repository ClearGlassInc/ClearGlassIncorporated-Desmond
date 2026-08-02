#!/usr/bin/env python3
# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Tests for lead routing bot."""
import json
import sys
from pathlib import Path

# Add bots to path
sys.path.insert(0, str(Path(__file__).parent.parent / "bots"))

from lead_routing_bot import HubSpotClient


def test_hubspot_create_contact_mock():
    """Test HubSpot contact creation in mock mode."""
    client = HubSpotClient(api_key="mock-key")
    result = client.create_or_update_contact(
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        company="Acme",
    )
    assert result["success"] is True
    assert result["email"] == "test@example.com"
    assert "contact_id" in result


def test_hubspot_set_property_mock():
    """Test HubSpot property setting in mock mode."""
    client = HubSpotClient(api_key="mock-key")
    result = client.set_contact_property(
        contact_id="12345",
        property_name="lead_type",
        value="employer",
    )
    assert result is True


def test_hubspot_with_no_key():
    """Test HubSpot client falls back to mock when no key provided."""
    client = HubSpotClient()
    result = client.create_or_update_contact(
        email="test@example.com",
        first_name="Jane",
    )
    assert result["success"] is True


def test_hubspot_multiple_contacts():
    """Test creating multiple contacts."""
    client = HubSpotClient()
    emails = ["alice@example.com", "bob@example.com", "carol@example.com"]
    results = []
    for email in emails:
        result = client.create_or_update_contact(
            email=email,
            first_name=email.split("@")[0],
        )
        results.append(result)
    
    assert len(results) == 3
    assert all(r["success"] for r in results)
    assert all(r["email"] == email for r, email in zip(results, emails))


def test_hubspot_contact_id_consistency():
    """Test that same email always produces same contact ID."""
    client = HubSpotClient()
    email = "test@example.com"
    
    result1 = client.create_or_update_contact(email=email)
    result2 = client.create_or_update_contact(email=email)
    
    assert result1["contact_id"] == result2["contact_id"]


if __name__ == "__main__":
    test_hubspot_create_contact_mock()
    test_hubspot_set_property_mock()
    test_hubspot_with_no_key()
    test_hubspot_multiple_contacts()
    test_hubspot_contact_id_consistency()
    print("All routing tests passed!")
