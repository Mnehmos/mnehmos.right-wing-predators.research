#!/usr/bin/env python3
"""
Add enrichments for dataset 10+ entries (IDs 893-1487)
Batch 1: High-profile and extremist cases
"""

import json

# New enrichments based on research
new_enrichments = [
    {
        "id": 897,
        "name": "Warren Jeffs",
        "year": 2011,
        "description": "FLDS (Fundamentalist Church of Jesus Christ of Latter Day Saints) leader Warren Jeffs was convicted in August 2011 of child rape and aggravated sexual assault of a minor for raping a 15-year-old child bride and a 12-year-old child bride. He was sentenced to life in prison plus 20 years. Texas authorities discovered over 700 pieces of evidence including priesthood records and audio tape of sexual assault.",
        "position": ["religious leader"],
        "crime": ["rape", "child molestation", "sexual abuse"],
        "tags": ["religious leader", "cult leader"]
    },
    {
        "id": 899,
        "name": "James Comer",
        "year": 1991,
        "description": "U.S. Representative James Comer (R-KY) was accused by ex-girlfriend Marilyn Thomas of domestic violence in the 1990s during their relationship at Western Kentucky University. Thomas claimed Comer hit her, was controlling and abusive, impregnated her, and forced her to get an abortion in November 1991. Comer denied the allegations but later admitted to leaking blogger emails to discredit her story.",
        "position": ["congress"],
        "crime": ["domestic violence", "sexual harassment"],
        "tags": ["congress", "republican"]
    },
    {
        "id": 900,
        "name": "Nathan Larson",
        "year": 2008,
        "description": "Far-right white supremacist and self-described pedophilia advocate Nathan Larson served 14 months in prison in 2008 for threatening the president. He created websites including 'suiped.org' and 'incelocalypse.today' to facilitate sharing of child sexual abuse material and pedophilia advocacy. In 2020, he was arrested at Denver International Airport for kidnapping a 12-year-old girl. He died in custody in September 2021 while facing federal felony charges for soliciting child pornography.",
        "position": [],
        "crime": ["child exploitation", "kidnapping", "child pornography"],
        "tags": ["white supremacist", "pedophile advocate"]
    },
    {
        "id": 901,
        "name": "James Mason",
        "year": 1994,
        "description": "White nationalist and influential neo-Nazi figure James Mason was arrested in the late 1980s-1990s and found to have nude images of a 15-year-old girl. In 1994, he was charged with sexual exploitation of a minor after police became aware he was dating a teenager. While initial charges were dropped, he eventually was convicted on weapons charges related to threatening a 16-year-old ex-girlfriend. Mason is best known as the author of 'Siege', an influential neo-Nazi manifesto advocating for white supremacist revolution through terrorism.",
        "position": [],
        "crime": ["child sexual abuse", "child pornography", "sexual exploitation"],
        "tags": ["white nationalist", "neo-nazi"]
    }
]

# Load existing enrichments
with open('/home/user/right-wing-predators/manual_enrichments.json', 'r', encoding='utf-8') as f:
    enrichments = json.load(f)

# Get existing IDs to avoid duplicates
existing_ids = {e['id'] for e in enrichments}

# Add only new enrichments
added_count = 0
for new_enrichment in new_enrichments:
    if new_enrichment['id'] not in existing_ids:
        enrichments.append(new_enrichment)
        added_count += 1
        existing_ids.add(new_enrichment['id'])
    else:
        print(f"Skipping ID {new_enrichment['id']} - already exists")

# Sort by ID
enrichments.sort(key=lambda x: x['id'])

# Save updated enrichments
with open('/home/user/right-wing-predators/manual_enrichments.json', 'w', encoding='utf-8') as f:
    json.dump(enrichments, f, indent=2, ensure_ascii=False)

print(f"Added {added_count} new enrichments")
print(f"Total enrichments now: {len(enrichments)}")
