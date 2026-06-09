# Orchestrator Handoff: Right-Wing Predators Data Transformation

## Task Objective
Transform all JSON data files in the `data/` directory into properly formatted Markdown files for use in a static site. The data contains information about right-wing individuals accused of sexual misconduct, abuse, or related crimes.

## Current Status

### Completed Work
- ✅ Analyzed data structure and format requirements
- ✅ Read all 16 data files to understand complete dataset
- ✅ Designed standardized markdown template for entries
- ✅ Transformed data-1.json → entries-001-100.md (entries 1-100)
- ✅ Transformed data-2.json → entries-094-193.md (entries 94-193)
- ✅ Transformed data-3.json → entries-194-293.md (entries 194-293)
- ✅ Transformed data-4.json → entries-294-393.md (entries 294-393)

### Remaining Work
The following data files still need to be transformed:
- data-5.json (entries 394-493)
- data-6.json (entries 494-593)
- data-7.json (entries 594-693)
- data-8.json (entries 694-793)
- data-9.json (entries 794-893)
- data-10.json (entries 894-993)
- data-11.json (entries 994-1093)
- data-12.json (entries 1094-1193)
- data-13.json (entries 1194-1293)
- data-14.json (entries 1294-1393)
- data-15.json (entries 1394-1493)
- data-16.json (entries 1494-1593)

### Final Steps
- Create master index file (entries-index.md)
- Verify all entries are properly formatted

## Standardized Entry Format

Each entry should follow this template:

```markdown
## Entry [ID]: [Name]

**Position:** [Position 1, Position 2, ...]  
**Crime:** [Crime 1, Crime 2, ...]  
**Year:** [Year or "Unknown"]

[Full description text]

**Sources:**  
- [Source URL 1]  
- [Source URL 2]  

**Tags:** [Tag 1, Tag 2, ...]

---
```

### Formatting Rules
1. **Entry Headers:** Use `## Entry [ID]: [Name]` format
2. **Metadata Fields:** Use bold labels with colons (e.g., `**Position:**`)
3. **Lists:** Use bullet points for sources and tags
4. **Separators:** Use `---` between entries
5. **Empty Values:** Use "Unknown" for missing/null values
6. **Truncated Descriptions:** Complete incomplete descriptions where obvious
7. **Clean Names:** Remove truncation artifacts from names
8. **URLs:** Ensure all source URLs are complete and properly formatted
9. **Year Handling:** Display actual year or "Unknown" for null values
10. **Tags:** Display as comma-separated list

## Subtask Breakdown Strategy

### Recommended Approach
Break the remaining work into **12 parallelizable subtasks** (one per remaining data file):

1. **Subtask 1:** Transform data-5.json → entries-394-493.md
2. **Subtask 2:** Transform data-6.json → entries-494-593.md
3. **Subtask 3:** Transform data-7.json → entries-594-693.md
4. **Subtask 4:** Transform data-8.json → entries-694-793.md
5. **Subtask 5:** Transform data-9.json → entries-794-893.md
6. **Subtask 6:** Transform data-10.json → entries-894-993.md
7. **Subtask 7:** Transform data-11.json → entries-994-1093.md
8. **Subtask 8:** Transform data-12.json → entries-1094-1193.md
9. **Subtask 9:** Transform data-13.json → entries-1194-1293.md
10. **Subtask 10:** Transform data-14.json → entries-1294-1393.md
11. **Subtask 11:** Transform data-15.json → entries-1394-1493.md
12. **Subtask 12:** Transform data-16.json → entries-1494-1593.md

### Final Subtask
13. **Subtask 13:** Create master index file (entries-index.md) that links to all entry files

## File Naming Convention
- Output files should be named: `entries-[START_ID]-[END_ID].md`
- Example: data-5.json (entries 394-493) → `entries-394-493.md`

## Workspace Context
- **Base Directory:** `f:/Github/mnehmos.right-wing-predators.research`
- **Data Directory:** `data/`
- **All data files are read-only** (use write_to_file to create new markdown files)
- **No file restrictions** in current mode

## Quality Assurance Checklist
For each subtask, ensure:
- [ ] All entries from the JSON file are included
- [ ] Entry IDs match the JSON data
- [ ] All fields (name, position, crime, description, sources, tags, year) are populated
- [ ] Empty/null values show as "Unknown"
- [ ] All source URLs are complete and valid
- [ ] Entries are separated by `---`
- [ ] File follows the standardized format
- [ ] No truncation artifacts remain in names or descriptions

## Dependencies
- No dependencies between subtasks (all can run in parallel)
- Final index subtask depends on all transformation subtasks being complete

## Estimated Complexity
- Each data file contains ~100 entries
- Each transformation subtask should take approximately 5-10 minutes
- Total estimated time for all subtasks: 60-120 minutes (parallelized)

## Example of Completed Work
Reference files for format consistency:
- `data/entries-001-100.md` (first 100 entries)
- `data/entries-094-193.md` (entries 94-193)
- `data/entries-294-393.md` (entries 294-393)

## Success Criteria
- All 16 data files transformed to markdown
- All ~1,600 entries properly formatted
- Master index file created with links to all entry files
- All files ready for static site generation
