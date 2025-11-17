#!/usr/bin/env python3
"""
Apply manual enrichments to the cleaned data
"""

import json

def apply_enrichments(
    data_file='data_cleaned.json',
    enrichments_file='manual_enrichments.json',
    output_file='data_enriched.json'
):
    """Merge manual enrichments into the dataset"""

    # Load cleaned data
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load enrichments
    with open(enrichments_file, 'r', encoding='utf-8') as f:
        enrichments = json.load(f)

    # Create lookup dict for enrichments by ID
    enrichments_dict = {e['id']: e for e in enrichments}

    # Apply enrichments
    enriched_count = 0
    for entry in data:
        if entry['id'] in enrichments_dict:
            enrichment = enrichments_dict[entry['id']]

            # Merge fields (enrichment takes precedence)
            for key, value in enrichment.items():
                if key != 'id':  # Don't override ID
                    if value:  # Only update if enrichment has a value
                        entry[key] = value

            enriched_count += 1

    print(f"Applied enrichments to {enriched_count} entries")

    # Save enriched data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved enriched data to {output_file}")

    return data

if __name__ == '__main__':
    apply_enrichments()
