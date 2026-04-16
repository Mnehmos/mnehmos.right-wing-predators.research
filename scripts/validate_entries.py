#!/usr/bin/env python3
"""Validate generated entry files have valid YAML frontmatter."""

import os
import yaml

ENTRIES_DIR = 'src/content/entries'

def main():
    files = [f for f in os.listdir(ENTRIES_DIR) if f.endswith('.md')]
    valid = 0
    invalid = []
    
    for filename in files:
        filepath = os.path.join(ENTRIES_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter between --- markers
            parts = content.split('---')
            if len(parts) < 3:
                invalid.append((filename, 'No frontmatter found'))
                continue
            
            frontmatter = parts[1].strip()
            data = yaml.safe_load(frontmatter)
            
            # Check required fields
            required = ['name', 'slug', 'positions', 'crimes', 'tags', 'sources']
            missing = [f for f in required if f not in data]
            if missing:
                invalid.append((filename, f'Missing fields: {missing}'))
                continue

            for field in ['positions', 'crimes', 'tags', 'sources']:
                if field not in data:
                    continue
                value = data[field]
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    invalid.append((filename, f'Field {field} must be a list of strings'))
                    break
            else:
                valid += 1
                continue
            
        except Exception as e:
            invalid.append((filename, str(e)[:60]))
    
    print(f'Validated {valid}/{len(files)} files successfully')
    
    if invalid:
        print(f'\nInvalid files ({len(invalid)}):')
        for filename, error in invalid[:10]:
            print(f'  {filename}: {error}')
        if len(invalid) > 10:
            print(f'  ... and {len(invalid) - 10} more')
    else:
        print('All files have valid YAML frontmatter!')

if __name__ == '__main__':
    main()
