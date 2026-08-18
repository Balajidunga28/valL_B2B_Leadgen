"""
Level 3 CLEAN Pipeline Test Script

Tests the Level 3 cleaning pipeline against existing raw_records in the database.
Verifies all audit requirements.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import async_session_factory, engine, Base
from app.services.level3 import run_clean
from app.services.clean import (
    standardize_name, normalize_phone, normalize_url,
    standardize_address, standardize_state, standardize_city,
    compute_completeness, clean_raw_data
)
from app.services.entity_resolution import resolve_entities
from sqlalchemy import text


async def test_cleaning_operations():
    """Test individual cleaning operations."""
    print("=" * 60)
    print("TEST 1: Cleaning Operations")
    print("=" * 60)

    # Name standardization
    tests = [
        ("Aayush Hospitals, Eluru", "Aayush Hospitals"),
        ("  SREE Multi Speciality Hospital  ", "Sree Multi Speciality Hospital"),
        ("Life Hospitals | Orthopedic Hospital in Eluru", "Life Hospitals"),
        ("District Hospital - Eluru", "District Hospital"),
        ("A.A Hospitals: Best Eye Hospital in Eluru", "A.A Hospitals"),
    ]
    print("\nName standardization:")
    for input_val, expected in tests:
        result = standardize_name(input_val)
        status = "OK" if result and expected.lower() in result.lower() else "FAIL"
        print(f"  [{status}] '{input_val}' -> '{result}'")

    # Phone normalization
    phone_tests = [
        ("095151 15103", "+919515115103"),
        ("088122 27755", "+918812227755"),
        ("+91 80 49653185", "+918049653185"),
        ("9876543210", "+919876543210"),
        ("080 49653185", "+918049653185"),
        (None, None),
        ("", None),
    ]
    print("\nPhone normalization:")
    for input_val, expected in phone_tests:
        result = normalize_phone(input_val)
        status = "OK" if result == expected else "FAIL"
        print(f"  [{status}] '{input_val}' -> '{result}' (expected: '{expected}')")

    # URL normalization
    url_tests = [
        ("https://example.com", "https://example.com"),
        ("http://example.com/", "https://example.com"),
        ("example.com", "https://example.com"),
        ("https://www.bing.com/ck/a?...", None),  # Bing tracking
        (None, None),
    ]
    print("\nURL normalization:")
    for input_val, expected in url_tests:
        result = normalize_url(input_val)
        status = "OK" if result == expected else "FAIL"
        print(f"  [{status}] '{input_val}' -> '{result}'")

    # State standardization
    state_tests = [
        ("AP", "Andhra Pradesh"),
        ("andhra pradesh", "Andhra Pradesh"),
        ("Telangana", "Telangana"),
        ("KA", "Karnataka"),
    ]
    print("\nState standardization:")
    for input_val, expected in state_tests:
        result = standardize_state(input_val)
        status = "OK" if result == expected else "FAIL"
        print(f"  [{status}] '{input_val}' -> '{result}'")

    # Completeness scoring
    print("\nCompleteness scoring:")
    full_record = {"name": "Test", "phone": "+911234567890", "address": "123 St",
                   "website": "https://test.com", "city": "Eluru",
                   "latitude": 16.7, "longitude": 81.1, "rating": 4.5}
    print(f"  Full record: {compute_completeness(full_record)}")
    empty_record = {"name": "Test"}
    print(f"  Name only: {compute_completeness(empty_record)}")
    no_record = {}
    print(f"  Empty: {compute_completeness(no_record)}")


async def test_sample_clean():
    """Test cleaning a small sample of real records."""
    print("\n" + "=" * 60)
    print("TEST 2: Clean Small Sample (5 records)")
    print("=" * 60)

    async with async_session_factory() as db:
        result = await db.execute(text(
            "SELECT id, source_adapter, raw_data FROM raw_records "
            "WHERE raw_data->>'name' IS NOT NULL LIMIT 5"
        ))
        rows = result.fetchall()

        for i, row in enumerate(rows):
            raw_data = row[1]  # raw_data is column index 2, but row[1] is source_adapter
            # Actually: row = (id, source_adapter, raw_data)
            rr_id = row[0]
            source = row[1]
            raw = row[2]

            cleaned = clean_raw_data(raw)
            print(f"\n  Record {i+1} (source={source}):")
            print(f"    name: '{raw.get('name')}' -> '{cleaned.get('name')}'")
            print(f"    phone: '{raw.get('phone')}' -> '{cleaned.get('phone')}'")
            print(f"    website: '{raw.get('website')}' -> '{cleaned.get('website')}'")
            print(f"    completeness: {cleaned.get('completeness_score')}")
            changes = cleaned.get("_level3_changes", [])
            if changes:
                for c in changes:
                    print(f"    change: {c}")
            else:
                print(f"    no changes")


async def test_entity_resolution():
    """Test entity resolution with known duplicates."""
    print("\n" + "=" * 60)
    print("TEST 3: Entity Resolution (synthetic duplicates)")
    print("=" * 60)

    # Create synthetic records that should be grouped
    test_records = [
        {"name": "Aayush Hospitals", "phone": "+918812227755", "city": "Eluru",
         "address": "123 Main St", "website": "https://aayush.com",
         "latitude": 16.71, "longitude": 81.11,
         "_raw_record_id": "raw_1", "_source_adapter": "google_search",
         "_source_record_id": "gmaps_abc"},
        {"name": "Aayush Hospitals, Eluru", "phone": "+918812227755", "city": "Eluru",
         "address": None, "website": None,
         "latitude": 16.71, "longitude": 81.11,
         "_raw_record_id": "raw_2", "_source_adapter": "openstreetmap",
         "_source_record_id": "osm_node_123"},
        {"name": "Aayush Hospital", "phone": None, "city": "Eluru",
         "address": "456 Hospital Rd", "website": None,
         "latitude": 16.72, "longitude": 81.12,
         "_raw_record_id": "raw_3", "_source_adapter": "web_search",
         "_source_record_id": "web_456"},
        {"name": "Life Hospitals", "phone": "+918074604425", "city": "Eluru",
         "address": "789 Health Ave", "website": "https://lifehospitals.com",
         "latitude": 16.70, "longitude": 81.10,
         "_raw_record_id": "raw_4", "_source_adapter": "google_search",
         "_source_record_id": "gmaps_def"},
        {"name": "Life Hospitals | Orthopedic", "phone": "+918074604425", "city": "Eluru",
         "address": None, "website": None,
         "latitude": 16.70, "longitude": 81.10,
         "_raw_record_id": "raw_5", "_source_adapter": "openstreetmap",
         "_source_record_id": "osm_node_789"},
    ]

    clusters = resolve_entities(test_records)
    print(f"\n  Input: {len(test_records)} records")
    print(f"  Output: {len(clusters)} entity clusters")
    for i, c in enumerate(clusters):
        print(f"\n  Entity {i+1}: '{c.best_name}'")
        print(f"    Sources: {c.source_adapters}")
        print(f"    Raw record IDs: {c.raw_record_ids}")
        print(f"    Phone: {c.best_phone}")
        print(f"    Duplicates of: {c.duplicate_of}")


async def test_full_pipeline():
    """Test the full Level 3 pipeline against ALL existing raw_records."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Level 3 Pipeline (all existing records)")
    print("=" * 60)

    async with async_session_factory() as db:
        # Get org_id
        result = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
        org_row = result.fetchone()
        if not org_row:
            print("  ERROR: No organizations found")
            return
        org_id = org_row[0]
        print(f"  Organization: {org_id}")

        # Count raw records before
        result = await db.execute(text(
            "SELECT COUNT(*) FROM raw_records WHERE organization_id = :org"
        ), {"org": org_id})
        raw_count_before = result.scalar()
        print(f"  Raw records before: {raw_count_before}")

        # Count companies before
        result = await db.execute(text(
            "SELECT COUNT(*) FROM companies WHERE organization_id = :org"
        ), {"org": org_id})
        companies_before = result.scalar()
        print(f"  Companies before: {companies_before}")

        # Run Level 3
        print("\n  Running Level 3 CLEAN pipeline...")
        summary = await run_clean(db=db, organization_id=org_id)

        print(f"\n  Results:")
        for k, v in summary.items():
            print(f"    {k}: {v}")

        # Verify raw records unchanged
        result = await db.execute(text(
            "SELECT COUNT(*) FROM raw_records WHERE organization_id = :org"
        ), {"org": org_id})
        raw_count_after = result.scalar()
        print(f"\n  Raw records after: {raw_count_after}")
        print(f"  Raw records unchanged: {raw_count_before == raw_count_after}")

        # Verify companies created
        result = await db.execute(text(
            "SELECT COUNT(*) FROM companies WHERE organization_id = :org"
        ), {"org": org_id})
        companies_after = result.scalar()
        print(f"  Companies after: {companies_after}")

        # Verify raw_records have company_id set
        result = await db.execute(text(
            "SELECT COUNT(*) FROM raw_records WHERE organization_id = :org AND company_id IS NOT NULL"
        ), {"org": org_id})
        linked = result.scalar()
        print(f"  Raw records linked to companies: {linked}")

        # Verify normalized_data populated
        result = await db.execute(text(
            "SELECT COUNT(*) FROM raw_records WHERE organization_id = :org AND normalized_data IS NOT NULL"
        ), {"org": org_id})
        normalized = result.scalar()
        print(f"  Raw records with normalized_data: {normalized}")

        # Sample a company
        result = await db.execute(text(
            "SELECT name, phone, website, city, state, completeness_score "
            "FROM companies WHERE organization_id = :org "
            "ORDER BY completeness_score DESC LIMIT 5"
        ), {"org": org_id})
        print(f"\n  Top 5 companies by completeness:")
        for row in result.fetchall():
            print(f"    {row[0]} | phone={row[1]} | website={row[2]} | city={row[3]} | state={row[4]} | score={row[5]}")

        # Sample a duplicate cluster
        result = await db.execute(text(
            "SELECT c.name, COUNT(rr.id) as raw_count "
            "FROM companies c "
            "JOIN raw_records rr ON rr.company_id = c.id "
            "WHERE c.organization_id = :org "
            "GROUP BY c.id, c.name "
            "HAVING COUNT(rr.id) > 1 "
            "ORDER BY raw_count DESC LIMIT 5"
        ), {"org": org_id})
        print(f"\n  Top duplicate clusters:")
        for row in result.fetchall():
            print(f"    '{row[0]}' -> {row[1]} raw records")


async def main():
    await test_cleaning_operations()
    await test_sample_clean()
    await test_entity_resolution()
    await test_full_pipeline()
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
