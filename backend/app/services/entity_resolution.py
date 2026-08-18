"""
url: /backend/app/services/entity_resolution.py
About:
  Level 3 entity resolution — identifies which raw records likely represent
  the same real-world business. Groups records into entity clusters without
  deleting any raw records. Each cluster becomes one Company record.

  Strategy:
  1. Exact match on source_record_id (same source, same ID)
  2. Exact match on normalized name + same city
  3. Exact match on phone number (same number = same business)
  4. Fuzzy name match (similarity >= 0.85) + same city
  5. Exact name match + nearby coordinates (within 1km)
"""

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.clean import name_for_matching, normalize_phone


@dataclass
class EntityCluster:
    """A group of raw records that likely represent the same business."""
    entity_id: str
    raw_record_ids: list[str] = field(default_factory=list)
    source_adapters: list[str] = field(default_factory=list)
    best_name: str | None = None
    best_phone: str | None = None
    best_address: str | None = None
    best_website: str | None = None
    best_city: str | None = None
    best_state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    rating: float | None = None
    review_count: int | None = None
    completeness_score: float = 0.0
    duplicate_of: list[str] = field(default_factory=list)


def _normalize_for_key(value: str | None) -> str:
    """Normalize a value for use as a grouping key."""
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(value).lower().strip())


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two lat/lng points in km."""
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _string_similarity(a: str, b: str) -> float:
    """Compute similarity between two strings using bigram overlap."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0

    def bigrams(s: str) -> set[str]:
        return {s[i:i+2] for i in range(len(s) - 1)}

    a_bigrams = bigrams(a)
    b_bigrams = bigrams(b)

    if not a_bigrams or not b_bigrams:
        return 0.0

    intersection = a_bigrams & b_bigrams
    return 2.0 * len(intersection) / (len(a_bigrams) + len(b_bigrams))


def _pick_best(records: list[dict], field_name: str) -> Any:
    """Pick the best value for a field from a list of records.

    Priority: non-None value with highest completeness, preferring values
    from records with more fields populated.
    """
    candidates = []
    for rec in records:
        val = rec.get(field_name)
        if val is not None and str(val).strip():
            # Score by how many other fields this record has
            fill_count = sum(1 for k in ["name", "phone", "address", "website", "city"]
                           if rec.get(k) and str(rec.get(k)).strip())
            candidates.append((fill_count, str(val).strip()))

    if not candidates:
        return None

    # Sort by fill count descending, pick best
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def resolve_entities(cleaned_records: list[dict[str, Any]]) -> list[EntityCluster]:
    """Group cleaned records into entity clusters.

    Args:
        cleaned_records: List of cleaned raw_data dicts, each must have
            '_raw_record_id' and '_source_adapter' keys.

    Returns:
        List of EntityCluster objects, each representing one deduplicated business.
    """
    if not cleaned_records:
        return []

    # --- Pass 1: Exact phone match ---
    phone_groups: dict[str, list[int]] = {}
    for i, rec in enumerate(cleaned_records):
        phone = normalize_phone(rec.get("phone"))
        if phone:
            phone_groups.setdefault(phone, []).append(i)

    # --- Pass 2: Exact normalized name + city match ---
    name_city_groups: dict[str, list[int]] = {}
    for i, rec in enumerate(cleaned_records):
        name_key = name_for_matching(rec.get("name"))
        city_key = _normalize_for_key(rec.get("city"))
        if name_key and len(name_key) >= 3:
            group_key = f"{name_key}|{city_key}"
            name_city_groups.setdefault(group_key, []).append(i)

    # --- Pass 3: Exact source_record_id ---
    source_id_groups: dict[str, list[int]] = {}
    for i, rec in enumerate(cleaned_records):
        src_id = rec.get("_source_record_id", "")
        if src_id:
            source_id_groups.setdefault(src_id, []).append(i)

    # Build union-find to merge groups that share records
    parent = list(range(len(cleaned_records)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Merge within each group
    for indices in source_id_groups.values():
        for i in range(1, len(indices)):
            union(indices[0], indices[i])

    for indices in phone_groups.values():
        for i in range(1, len(indices)):
            union(indices[0], indices[i])

    for indices in name_city_groups.values():
        for i in range(1, len(indices)):
            union(indices[0], indices[i])

    # --- Pass 4: Fuzzy name match + same city ---
    # Build clusters from current unions
    temp_clusters: dict[int, list[int]] = {}
    for i in range(len(cleaned_records)):
        root = find(i)
        temp_clusters.setdefault(root, []).append(i)

    # Group clusters by city to avoid cross-city comparisons
    city_to_clusters: dict[str, list[tuple[int, list[int]]]] = {}
    for root, members in temp_clusters.items():
        member_records = [cleaned_records[i] for i in members]
        city_key = _normalize_for_key(_pick_best(member_records, "city"))
        if not city_key:
            city_key = "_unknown_"
        city_to_clusters.setdefault(city_key, []).append((root, members))

    # Only fuzzy-match within same city
    for city_key, cluster_list in city_to_clusters.items():
        for ci, (root_a, members_a) in enumerate(cluster_list):
            name_a = name_for_matching(_pick_best(
                [cleaned_records[i] for i in members_a], "name"
            ))
            if not name_a or len(name_a) < 3:
                continue

            for cj in range(ci + 1, len(cluster_list)):
                root_b, members_b = cluster_list[cj]
                name_b = name_for_matching(_pick_best(
                    [cleaned_records[i] for i in members_b], "name"
                ))
                if not name_b or len(name_b) < 3:
                    continue

                sim = _string_similarity(name_a, name_b)
                if sim >= 0.85:
                    union(root_a, root_b)

    # --- Pass 5: Coordinate proximity (within 1km) + similar name ---
    # Grid-based spatial bucketing: ~0.01 degree grid (~1km)
    # Only compare records within same or adjacent grid cells
    import math
    grid_size = 0.01  # ~1km
    grid: dict[tuple[int, int], list[int]] = {}
    for i in range(len(cleaned_records)):
        lat = cleaned_records[i].get("latitude")
        lng = cleaned_records[i].get("longitude")
        if not lat or not lng:
            continue
        gx = int(math.floor(float(lat) / grid_size))
        gy = int(math.floor(float(lng) / grid_size))
        grid.setdefault((gx, gy), []).append(i)

    # For each cell, compare with itself and 8 neighbors
    processed_pairs: set[tuple[int, int]] = set()
    for (gx, gy), cell_indices in grid.items():
        neighbor_indices = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neighbor_indices.extend(grid.get((gx + dx, gy + dy), []))

        for i in cell_indices:
            lat_i = cleaned_records[i].get("latitude")
            lng_i = cleaned_records[i].get("longitude")
            if not lat_i or not lng_i:
                continue
            name_i = name_for_matching(cleaned_records[i].get("name"))
            if not name_i or len(name_i) < 3:
                continue

            for j in neighbor_indices:
                if j <= i:
                    continue
                pair = (i, j)
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)

                if find(i) == find(j):
                    continue

                lat_j = cleaned_records[j].get("latitude")
                lng_j = cleaned_records[j].get("longitude")
                if not lat_j or not lng_j:
                    continue
                name_j = name_for_matching(cleaned_records[j].get("name"))
                if not name_j or len(name_j) < 3:
                    continue

                dist = _haversine_km(lat_i, lng_i, lat_j, lng_j)
                if dist <= 1.0:
                    sim = _string_similarity(name_i, name_j)
                    if sim >= 0.70:
                        union(i, j)

    # --- Build final clusters ---
    final_groups: dict[int, list[int]] = {}
    for i in range(len(cleaned_records)):
        root = find(i)
        final_groups.setdefault(root, []).append(i)

    clusters = []
    for idx, (root, members) in enumerate(final_groups.items()):
        member_records = [cleaned_records[i] for i in members]

        cluster = EntityCluster(
            entity_id=f"entity_{idx}",
            raw_record_ids=[r.get("_raw_record_id", "") for r in member_records],
            source_adapters=list({r.get("_source_adapter", "unknown") for r in member_records}),
            best_name=_pick_best(member_records, "name"),
            best_phone=_pick_best(member_records, "phone"),
            best_address=_pick_best(member_records, "address"),
            best_website=_pick_best(member_records, "website"),
            best_city=_pick_best(member_records, "city"),
            best_state=_pick_best(member_records, "state"),
            completeness_score=max(
                (r.get("completeness_score", 0) for r in member_records), default=0
            ),
        )

        # Pick best lat/lng (from record with most data)
        for rec in sorted(member_records,
                         key=lambda r: sum(1 for k in ["name", "phone", "address", "website"]
                                          if r.get(k)), reverse=True):
            if rec.get("latitude") and rec.get("longitude"):
                cluster.latitude = rec["latitude"]
                cluster.longitude = rec["longitude"]
                break

        # Pick best rating
        for rec in member_records:
            if rec.get("rating") is not None:
                cluster.rating = rec["rating"]
                if rec.get("reviews_count"):
                    cluster.review_count = rec["reviews_count"]
                break

        # If multiple records, they are duplicates of each other
        if len(member_records) > 1:
            cluster.duplicate_of = cluster.raw_record_ids[1:]

        clusters.append(cluster)

    return clusters
