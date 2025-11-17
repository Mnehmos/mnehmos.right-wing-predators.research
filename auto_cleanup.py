#!/usr/bin/env python3
"""
Automated data cleanup and enrichment script
Fixes common issues and extracts information from descriptions
"""

import json
import re
from datetime import datetime

def extract_year_from_text(text):
    """Extract year from text (description or sources)"""
    if not text:
        return None

    # Look for year patterns (1990-2025)
    year_patterns = [
        r'\b(19\d{2}|20[0-2]\d)\b',  # 1900-2029
        r"'(\d{2})\b",  # '98, '03, etc.
    ]

    years = []
    for pattern in year_patterns:
        matches = re.findall(pattern, str(text))
        for match in matches:
            if len(match) == 2:  # Handle '98 format
                year = int(match)
                # Convert to full year (assume 1900s for > 50, 2000s for <= 50)
                year = 1900 + year if year > 50 else 2000 + year
            else:
                year = int(match)

            # Only accept reasonable years for this database
            if 1970 <= year <= 2024:
                years.append(year)

    # Return the most recent year found (likely the conviction/accusation date)
    return max(years) if years else None

def clean_name(name):
    """Clean up name field - extract actual person name"""
    if not name:
        return name

    # Remove common prefixes
    prefixes_to_remove = [
        r'^Republican\s+',
        r'^GOP\s+',
        r'^Former\s+',
        r'^Ex-',
    ]

    cleaned = name
    for prefix in prefixes_to_remove:
        cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)

    # Check if name contains position descriptions
    position_keywords = [
        'chairman', 'mayor', 'senator', 'representative', 'congressman',
        'judge', 'pastor', 'minister', 'activist', 'official', 'candidate',
        'governor', 'lobbyist', 'staffer', 'director', 'commissioner',
        'legislator', 'councilman', 'constable', 'sheriff'
    ]

    # If name contains position, try to extract actual name
    lower_name = cleaned.lower()
    has_position = any(keyword in lower_name for keyword in position_keywords)

    if has_position:
        # Try to extract name after position
        # Pattern: "Position Name" or "Name, Position"
        parts = re.split(r'\s+(?:of|for|from|in)\s+', cleaned, maxsplit=1)
        if len(parts) > 1:
            # Take the part before location/context
            cleaned = parts[0]

        # Extract capitalized words that look like names
        words = cleaned.split()
        name_words = []
        for word in words:
            # Skip position words
            if word.lower() not in position_keywords and word[0].isupper():
                name_words.append(word)

        if name_words:
            cleaned = ' '.join(name_words)

    return cleaned.strip()

def extract_crimes_from_description(description):
    """Extract crime types from description text"""
    if not description:
        return []

    description_lower = description.lower()

    crime_patterns = {
        'rape': r'\b(rape|raped|raping)\b',
        'sexual assault': r'\b(sexual assault|sexually assault)',
        'sexual abuse': r'\b(sexual abuse|sexually abus)',
        'child molestation': r'\b(child molestation|molest|fondl)',
        'child pornography': r'\b(child porn|kiddie porn)',
        'sexual harassment': r'\b(sexual harassment|harass)',
        'assault': r'\b(assault|batter)',
        'domestic violence': r'\b(domestic violence|domestic abuse)',
        'violence': r'\b(violence|violent)',
        'child exploitation': r'\b(child exploit|child sex)',
        'prostitution': r'\b(prostitution|soliciting)',
        'sodomy': r'\b(sodomy)',
        'kidnapping': r'\b(kidnap)',
        'sexual trafficking': r'\b(trafficking|sex trafficking)',
    }

    crimes_found = []
    for crime, pattern in crime_patterns.items():
        if re.search(pattern, description_lower):
            crimes_found.append(crime)

    return crimes_found

def auto_enrich_entry(entry):
    """Apply automated enrichment to a single entry"""
    enriched = entry.copy()

    # Extract year if missing
    if not enriched.get('year'):
        # Try description first
        year = extract_year_from_text(enriched.get('description', ''))
        if not year and enriched.get('sources'):
            # Try sources
            year = extract_year_from_text(' '.join(enriched.get('sources', [])))
        enriched['year'] = year

    # Clean name
    if enriched.get('name'):
        enriched['name'] = clean_name(enriched['name'])

    # Extract crimes if missing
    if not enriched.get('crime') or len(enriched.get('crime', [])) == 0:
        crimes = extract_crimes_from_description(enriched.get('description', ''))
        if crimes:
            enriched['crime'] = crimes

    return enriched

def auto_cleanup_data(input_file='data.json', output_file='data_cleaned.json'):
    """Run automated cleanup on entire dataset"""

    print("Loading data...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Processing {len(data)} entries...")

    stats = {
        'years_added': 0,
        'names_cleaned': 0,
        'crimes_added': 0,
    }

    enriched_data = []
    for i, entry in enumerate(data):
        original = entry.copy()
        enriched = auto_enrich_entry(entry)

        # Track changes
        if not original.get('year') and enriched.get('year'):
            stats['years_added'] += 1
        if original.get('name') != enriched.get('name'):
            stats['names_cleaned'] += 1
        if (not original.get('crime') or len(original.get('crime', [])) == 0) and enriched.get('crime'):
            stats['crimes_added'] += 1

        enriched_data.append(enriched)

        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(data)} entries...")

    print(f"\nAutomated cleanup complete!")
    print(f"  Years added: {stats['years_added']}")
    print(f"  Names cleaned: {stats['names_cleaned']}")
    print(f"  Crimes added: {stats['crimes_added']}")

    # Save cleaned data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {output_file}")

    return enriched_data, stats

if __name__ == '__main__':
    auto_cleanup_data()
