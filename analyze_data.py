#!/usr/bin/env python3
"""
Analyze data quality and identify standardization opportunities
"""

import json
from collections import Counter
from pprint import pprint

def analyze_data(input_file='data.json'):
    """Analyze the data for completeness and consistency"""

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = len(data)

    # Field completeness
    stats = {
        'total_entries': total,
        'with_name': sum(1 for e in data if e.get('name')),
        'with_position': sum(1 for e in data if e.get('position') and len(e['position']) > 0),
        'with_crime': sum(1 for e in data if e.get('crime') and len(e['crime']) > 0),
        'with_description': sum(1 for e in data if e.get('description')),
        'with_sources': sum(1 for e in data if e.get('sources') and len(e['sources']) > 0),
        'with_tags': sum(1 for e in data if e.get('tags') and len(e['tags']) > 0),
        'with_year': sum(1 for e in data if e.get('year')),
    }

    # Missing data
    stats['missing_name'] = total - stats['with_name']
    stats['missing_position'] = total - stats['with_position']
    stats['missing_crime'] = total - stats['with_crime']
    stats['missing_description'] = total - stats['with_description']
    stats['missing_sources'] = total - stats['with_sources']
    stats['missing_tags'] = total - stats['with_tags']
    stats['missing_year'] = total - stats['with_year']

    print("=" * 60)
    print("DATA QUALITY ANALYSIS")
    print("=" * 60)
    print(f"\nTotal Entries: {total}\n")

    print("Field Completeness:")
    print(f"  Name:        {stats['with_name']:4d} ({stats['with_name']/total*100:5.1f}%) | Missing: {stats['missing_name']}")
    print(f"  Position:    {stats['with_position']:4d} ({stats['with_position']/total*100:5.1f}%) | Missing: {stats['missing_position']}")
    print(f"  Crime:       {stats['with_crime']:4d} ({stats['with_crime']/total*100:5.1f}%) | Missing: {stats['missing_crime']}")
    print(f"  Description: {stats['with_description']:4d} ({stats['with_description']/total*100:5.1f}%) | Missing: {stats['missing_description']}")
    print(f"  Sources:     {stats['with_sources']:4d} ({stats['with_sources']/total*100:5.1f}%) | Missing: {stats['missing_sources']}")
    print(f"  Tags:        {stats['with_tags']:4d} ({stats['with_tags']/total*100:5.1f}%) | Missing: {stats['missing_tags']}")
    print(f"  Year:        {stats['with_year']:4d} ({stats['with_year']/total*100:5.1f}%) | Missing: {stats['missing_year']}")

    # Analyze unique values
    all_positions = []
    all_crimes = []
    all_tags = []

    for entry in data:
        if entry.get('position'):
            all_positions.extend(entry['position'])
        if entry.get('crime'):
            all_crimes.extend(entry['crime'])
        if entry.get('tags'):
            all_tags.extend(entry['tags'])

    position_counts = Counter(all_positions)
    crime_counts = Counter(all_crimes)
    tag_counts = Counter(all_tags)

    print(f"\n{'-'*60}")
    print("UNIQUE VALUES")
    print(f"{'-'*60}")
    print(f"Unique Positions: {len(position_counts)}")
    print(f"Unique Crimes:    {len(crime_counts)}")
    print(f"Unique Tags:      {len(tag_counts)}")

    print(f"\n{'-'*60}")
    print("TOP 20 POSITIONS")
    print(f"{'-'*60}")
    for pos, count in position_counts.most_common(20):
        print(f"  {pos:30s} : {count:4d}")

    print(f"\n{'-'*60}")
    print("TOP 20 CRIMES")
    print(f"{'-'*60}")
    for crime, count in crime_counts.most_common(20):
        print(f"  {crime:40s} : {count:4d}")

    print(f"\n{'-'*60}")
    print("TOP 20 TAGS")
    print(f"{'-'*60}")
    for tag, count in tag_counts.most_common(20):
        print(f"  {tag:30s} : {count:4d}")

    # Sample entries with issues
    print(f"\n{'-'*60}")
    print("SAMPLE ENTRIES WITH MISSING DATA")
    print(f"{'-'*60}")

    # Entries missing crimes
    missing_crime = [e for e in data if not e.get('crime') or len(e['crime']) == 0]
    if missing_crime:
        print(f"\nEntries missing crime ({len(missing_crime)} total):")
        for entry in missing_crime[:5]:
            print(f"  ID {entry['id']}: {entry.get('name', 'NO NAME')[:50]}")

    # Entries missing year
    missing_year = [e for e in data if not e.get('year')]
    if missing_year:
        print(f"\nEntries missing year ({len(missing_year)} total):")
        for entry in missing_year[:5]:
            print(f"  ID {entry['id']}: {entry.get('name', 'NO NAME')[:50]}")

    # Entries with incomplete names
    incomplete_names = [e for e in data if e.get('name') and
                       ('Republican' in e['name'] or 'GOP' in e['name']) and
                       not any(word in e['name'].lower() for word in ['convicted', 'pleaded', 'accused'])]
    if incomplete_names:
        print(f"\nEntries with potentially incomplete names ({len(incomplete_names)} total):")
        for entry in incomplete_names[:10]:
            print(f"  ID {entry['id']}: {entry.get('name', 'NO NAME')[:70]}")

    # Description length analysis
    desc_lengths = [len(e.get('description', '')) for e in data]
    avg_desc = sum(desc_lengths) / len(desc_lengths)
    short_descs = [e for e in data if len(e.get('description', '')) < 100]

    print(f"\n{'-'*60}")
    print("DESCRIPTION ANALYSIS")
    print(f"{'-'*60}")
    print(f"Average description length: {avg_desc:.0f} characters")
    print(f"Entries with short descriptions (<100 chars): {len(short_descs)}")
    if short_descs:
        print("\nSample short descriptions:")
        for entry in short_descs[:5]:
            desc = entry.get('description', '')
            print(f"  ID {entry['id']}: {desc[:80]}...")

    print(f"\n{'='*60}")

if __name__ == '__main__':
    analyze_data()
