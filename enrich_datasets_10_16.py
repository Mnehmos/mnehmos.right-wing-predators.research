#!/usr/bin/env python3
"""
Extract and improve data from datasets 10-16 for enrichment
"""

import json
import os
from pathlib import Path

def extract_full_name(entry):
    """Try to extract full name from description if name is truncated"""
    name = entry.get('name', '').strip()
    description = entry.get('description', '')

    # List of common truncations to watch for
    truncations = {
        'August Kre': 'August Kreis',
        'August Kreins': 'August Kreins',
        'Chr': ['Christopher', 'Christian', 'Chris'],
        'Denn': ['Dennis', 'Dennison'],
        'Bor': ['Boris'],
        'Mat': ['Matthew', 'Martin'],
        'Ben': ['Benjamin'],
        'Therap': ['Therapist'],
        'Bapt': ['Baptist'],
        'Min': ['Minister'],
        'Assoc': ['Associate'],
        'Assoc.': ['Associate'],
        'Supt': ['Superintendent'],
        'Comm': ['Commissioner', 'Committee'],
        'Gov': ['Governor'],
        'Pres': ['President'],
        'Dir': ['Director'],
        'Del': ['Delegate'],
    }

    # If name ends with comma, it's likely truncated
    if name.endswith(','):
        # Try to extract from description
        words = description.split()
        if words:
            # Look for likely name patterns in first sentence
            for i, word in enumerate(words[:20]):
                if ',' in word or 'named' in description.lower():
                    if i > 0:
                        candidate = ' '.join(words[:i+2])
                        return candidate
        return name.rstrip(',')

    return name

def improve_entry(entry):
    """Improve data quality of an entry"""
    improved = entry.copy()

    # Fix truncated names
    improved['name'] = extract_full_name(entry)

    # Fill in missing crime if description suggests it
    if not improved.get('crime') or len(improved['crime']) == 0:
        desc = improved.get('description', '').lower()
        crimes = []

        crime_keywords = {
            'rape': ['rape', 'raped'],
            'sexual abuse': ['sexual abuse', 'sexually abused', 'sexual contact'],
            'child molestation': ['molestation', 'molested'],
            'child pornography': ['pornography', 'child porn', 'csam'],
            'sexual harassment': ['harassment', 'harassed', 'groped'],
            'assault': ['assault', 'assault'],
            'child exploitation': ['exploitation', 'exploited'],
            'domestic violence': ['domestic violence', 'domestic'],
            'kidnapping': ['kidnapping', 'kidnapped'],
            'prostitution': ['prostitution', 'soliciting'],
        }

        for crime, keywords in crime_keywords.items():
            for keyword in keywords:
                if keyword in desc:
                    if crime not in crimes:
                        crimes.append(crime)
                    break

        if crimes:
            improved['crime'] = crimes

    # Sanitize year
    if not improved.get('year'):
        improved['year'] = None

    return improved

def process_datasets_10_16():
    """Extract and process all datasets 10-16"""
    base_path = Path('/home/user/right-wing-predators/data')
    all_enrichments = []

    # Load existing enrichments to avoid duplicates
    enrichments_path = Path('/home/user/right-wing-predators/manual_enrichments.json')
    existing_ids = set()
    if enrichments_path.exists():
        with open(enrichments_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            existing_ids = {e['id'] for e in existing}

    # Process datasets 10-16
    for dataset_num in range(10, 17):
        file_path = base_path / f'data-{dataset_num}.json'

        if not file_path.exists():
            print(f"Skipping {file_path} - not found")
            continue

        print(f"Processing {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for entry in data:
            entry_id = entry.get('id')

            # Skip if already in enrichments or invalid ID
            if entry_id in existing_ids or not entry_id or isinstance(entry_id, int) and entry_id > 10000:
                continue

            # Skip placeholder/malformed entries
            if entry.get('name') in ['html', 'pdf', 'text', '']:
                continue

            # Improve the entry
            improved = improve_entry(entry)

            # Create enrichment record
            enrichment = {
                'id': entry_id,
                'name': improved.get('name', ''),
                'year': improved.get('year'),
                'description': improved.get('description', ''),
                'position': improved.get('position', []),
                'crime': improved.get('crime', []),
                'tags': improved.get('tags', []),
            }

            # Only add if we have meaningful data
            if enrichment['name'] and len(enrichment['name']) > 2:
                all_enrichments.append(enrichment)
                existing_ids.add(entry_id)

    print(f"\nExtracted {len(all_enrichments)} new enrichments from datasets 10-16")

    # Load existing enrichments
    with open(enrichments_path, 'r', encoding='utf-8') as f:
        existing_enrichments = json.load(f)

    # Combine and save
    all_enrichments = existing_enrichments + all_enrichments

    # Sort by ID for easier reading
    all_enrichments.sort(key=lambda x: x['id'])

    with open(enrichments_path, 'w', encoding='utf-8') as f:
        json.dump(all_enrichments, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(all_enrichments)} total enrichments to {enrichments_path}")

    return all_enrichments

if __name__ == '__main__':
    enrichments = process_datasets_10_16()
    print(f"\nCompleted! Added {len(enrichments)} enrichments")
