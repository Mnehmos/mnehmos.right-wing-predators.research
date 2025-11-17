#!/usr/bin/env python3
"""
Identify entries that still need manual research
Prioritize by importance/completeness
"""

import json

def analyze_cleaned_data(input_file='data_cleaned.json'):
    """Analyze what still needs work"""

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Categorize entries needing work
    high_priority = []  # Well-known figures, congress, governors
    missing_year = []
    missing_crime = []
    short_description = []
    incomplete_name = []

    high_priority_keywords = [
        'trump', 'moore', 'jordan', 'hastert', 'foley', 'gaetz',
        'speaker', 'senator', 'congressman', 'governor', 'attorney general'
    ]

    for entry in data:
        name = entry.get('name', '').lower()
        desc = entry.get('description', '')

        # Check if high priority
        is_high_priority = any(keyword in name or keyword in desc.lower()
                              for keyword in high_priority_keywords)

        if is_high_priority:
            high_priority.append(entry)

        # Track specific issues
        if not entry.get('year'):
            missing_year.append(entry)

        if not entry.get('crime') or len(entry.get('crime', [])) == 0:
            missing_crime.append(entry)

        if len(desc) < 100:
            short_description.append(entry)

        # Check for incomplete names
        if (len(name) < 3 or
            name.endswith('comm') or
            name.endswith('leg') or
            'republican' in name.lower()):
            incomplete_name.append(entry)

    print("=" * 70)
    print("ENTRIES REQUIRING MANUAL RESEARCH")
    print("=" * 70)

    print(f"\nHIGH PRIORITY (well-known figures): {len(high_priority)}")
    print("\nTop 20 high-priority entries:")
    for i, entry in enumerate(high_priority[:20], 1):
        year_str = f"({entry.get('year')})" if entry.get('year') else "(NO YEAR)"
        crime_str = f"{len(entry.get('crime', []))} crimes" if entry.get('crime') else "NO CRIMES"
        print(f"  {i:2d}. ID {entry['id']:4d}: {entry.get('name', 'NO NAME')[:40]:40s} {year_str:8s} {crime_str}")

    print(f"\n{'-'*70}")
    print(f"Still missing YEAR: {len(missing_year)}")
    print("Sample entries missing year:")
    for entry in missing_year[:10]:
        print(f"  ID {entry['id']:4d}: {entry.get('name', 'NO NAME')[:50]}")

    print(f"\n{'-'*70}")
    print(f"Still missing CRIME: {len(missing_crime)}")
    print("Sample entries missing crime:")
    for entry in missing_crime[:10]:
        print(f"  ID {entry['id']:4d}: {entry.get('name', 'NO NAME')[:50]}")

    print(f"\n{'-'*70}")
    print(f"INCOMPLETE NAMES: {len(incomplete_name)}")
    print("Sample incomplete names:")
    for entry in incomplete_name[:10]:
        print(f"  ID {entry['id']:4d}: {entry.get('name', 'NO NAME')}")

    print(f"\n{'-'*70}")
    print(f"SHORT DESCRIPTIONS (<100 chars): {len(short_description)}")

    print(f"\n{'='*70}")

    # Export high priority list for manual research
    with open('high_priority_research.json', 'w', encoding='utf-8') as f:
        json.dump(high_priority, f, indent=2, ensure_ascii=False)

    print(f"\nExported {len(high_priority)} high-priority entries to high_priority_research.json")

    return {
        'high_priority': high_priority,
        'missing_year': missing_year,
        'missing_crime': missing_crime,
        'short_description': short_description,
        'incomplete_name': incomplete_name
    }

if __name__ == '__main__':
    analyze_cleaned_data()
