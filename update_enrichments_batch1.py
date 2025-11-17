#!/usr/bin/env python3
"""
Update existing enrichments with new research data
"""

import json

# Updates to apply - keyed by ID
updates = {
    897: {
        "name": "Warren Jeffs",
        "year": 2011,
        "description": "FLDS (Fundamentalist Church of Jesus Christ of Latter Day Saints) leader Warren Jeffs was convicted in August 2011 of child rape and aggravated sexual assault of a minor for raping a 15-year-old child bride and a 12-year-old child bride. He was sentenced to life in prison plus 20 years. Texas authorities discovered over 700 pieces of evidence including priesthood records and audio tape of sexual assault."
    },
    899: {
        "name": "James Comer",
        "year": 1991,
        "description": "U.S. Representative James Comer (R-KY) was accused by ex-girlfriend Marilyn Thomas of domestic violence in the 1990s. Thomas claimed Comer hit her, was controlling and abusive, impregnated her, and forced her to get an abortion in November 1991. Comer denied allegations but later admitted to leaking emails to discredit her story."
    },
    900: {
        "name": "Nathan Larson",
        "year": 2008,
        "description": "Far-right white supremacist and self-described pedophilia advocate Nathan Larson served 14 months in prison in 2008 for threatening the president. He created websites to facilitate sharing of child sexual abuse material and pedophilia advocacy. In 2020, he was arrested for kidnapping a 12-year-old girl. He died in custody in September 2021 while facing federal charges for soliciting child pornography."
    },
    901: {
        "name": "James Mason",
        "year": 1994,
        "description": "White nationalist and influential neo-Nazi figure James Mason was arrested in the late 1980s-1990s and found to have nude images of a 15-year-old girl. In 1994, he was charged with sexual exploitation of a minor. He was convicted on weapons charges. Mason is best known as author of 'Siege', influential neo-Nazi manifesto advocating for white supremacist revolution."
    }
}

# Load enrichments
with open('/home/user/right-wing-predators/manual_enrichments.json', 'r', encoding='utf-8') as f:
    enrichments = json.load(f)

# Update matching entries
updated_count = 0
for entry in enrichments:
    if entry['id'] in updates:
        update_data = updates[entry['id']]
        for key, value in update_data.items():
            entry[key] = value
        updated_count += 1
        print(f"Updated ID {entry['id']}: {entry['name']}")

# Save updated enrichments
with open('/home/user/right-wing-predators/manual_enrichments.json', 'w', encoding='utf-8') as f:
    json.dump(enrichments, f, indent=2, ensure_ascii=False)

print(f"\nUpdated {updated_count} enrichments")
print(f"Total enrichments: {len(enrichments)}")
