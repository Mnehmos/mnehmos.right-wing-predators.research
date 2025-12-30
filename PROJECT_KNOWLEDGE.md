# Right-Wing Misconduct Database - Knowledge Base Document

## Quick Reference

| Property | Value |
|----------|-------|
| **Repository** | https://github.com/Mnehmos/mnehmos.right-wing-predators.research |
| **Primary Language** | Python / HTML/CSS/JavaScript |
| **Project Type** | Research / Web Application |
| **Status** | Active |
| **Last Updated** | 2025-12-29 |

## Overview

The Right-Wing Misconduct Database is a comprehensive, searchable web application that catalogues 1,506 documented allegations and convictions of misconduct involving right-wing individuals. The project combines a rich JSON dataset with a sophisticated single-page web application featuring real-time search, multi-dimensional filtering, CSV export capabilities, and optimized data loading for performance. It serves as a research tool and reference database for journalists, researchers, and the public to access documented cases with verifiable sources.

## Architecture

### System Design

This is a static web application that runs entirely in the browser using vanilla JavaScript with no external dependencies. The architecture follows a client-side data processing pattern where JSON data files are loaded dynamically and processed in-browser. The system uses a split-file strategy to optimize loading performance, dividing 1,506 entries into 16 separate JSON files (~100 entries each) that are loaded in parallel. Python utility scripts handle data management, analysis, and file splitting operations. The application can be served via any standard HTTP server (Python http.server, Node.js http-server, or PHP built-in server).

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| Main Web Interface | Single-page application with search, filtering, pagination | `index.html` |
| Data Files | Split JSON files containing 1,506 entries in 16 chunks | `data/data-*.json` |
| Data Index | Manifest file listing all data files and metadata | `data/index.json` |
| Legacy Data File | Original monolithic JSON backup | `data.json` |
| Data Splitter | Python script to split large JSON into optimized chunks | `split_data.py` |
| Data Analyzer | Python script to analyze data quality and completeness | `analyze_data.py` |
| Research Identifier | Script to identify entries needing manual research | `identify_research_needed.py` |
| Enrichment Applier | Script to apply manual data enrichments | `apply_enrichments.py` |
| Auto Cleanup | Script for automated data cleanup operations | `auto_cleanup.py` |
| Manual Enrichments | JSON file storing manual data corrections | `manual_enrichments.json` |
| Server Scripts | Shell scripts to start local web server | `serve.sh`, `serve.bat` |

### Data Flow

```
User Opens Browser → index.html loads
    ↓
JavaScript fetches data/index.json
    ↓
Parallel fetch of 16 data files (data/data-1.json through data-16.json)
    ↓
Data merged and loaded into memory (1,506 entries)
    ↓
User Interactions → Search/Filter/Sort operations
    ↓
In-memory filtering and pagination
    ↓
DOM rendering with highlighted search terms
    ↓
Optional: Export filtered results to CSV
```

## API Surface

### Public Interfaces

This is a frontend-only application with no server-side API. All functionality is exposed through the web interface and Python utility scripts.

#### Web Interface Functions

The HTML/JavaScript application exposes these primary functions:

- **loadData()**: Asynchronously loads split JSON data files or falls back to monolithic file
- **applyFilters()**: Filters dataset based on search term and dropdown selections
- **applySort()**: Sorts filtered data by ID, name, or year
- **displayCurrentPage()**: Renders current page of results with pagination
- **exportToCSV()**: Exports filtered results to downloadable CSV file
- **highlightText(text, searchTerm)**: Highlights search terms in result text

#### Python Utility Scripts

##### Script: `split_data.py`
- **Purpose**: Split data.json into optimized chunks for web loading
- **Parameters**:
  - `input_file` (string): Path to source JSON file (default: `data.json`)
  - `output_dir` (string): Directory for split files (default: `data/`)
  - `entries_per_file` (number): Entries per chunk (default: 100)
- **Returns**: Creates 16 JSON files plus index.json manifest

##### Script: `analyze_data.py`
- **Purpose**: Analyze data completeness, quality, and identify issues
- **Parameters**:
  - `input_file` (string): Path to JSON file to analyze (default: `data.json`)
- **Returns**: Console output with statistics on field completeness, unique values, and data quality issues

##### Script: `identify_research_needed.py`
- **Purpose**: Identify high-priority entries needing manual research
- **Parameters**:
  - `input_file` (string): Path to JSON file (default: `data_cleaned.json`)
- **Returns**: Creates `high_priority_research.json` with entries needing attention

### Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `itemsPerPage` | number | 25 | Number of entries displayed per page (options: 10, 25, 50, 100, all) |
| `DEBOUNCE_DELAY` | number | 300 | Milliseconds to wait before applying search filter (performance optimization) |
| `entries_per_file` | number | 100 | Number of database entries per split JSON file |
| `max_chars` | number | 2000 | Character limit for individual entry fields (from line numbers in Read tool) |

## Usage Examples

### Basic Usage - Starting the Web Application

```bash
# Using Python (recommended)
cd mnehmos.right-wing-predators.research
python3 -m http.server 8000

# Then open browser to: http://127.0.0.1:8000/
```

### Advanced Patterns - Regenerating Split Data Files

```python
# After editing data.json, regenerate optimized split files
python3 split_data.py

# Output:
# Reading data.json...
# Sorting entries by ID...
# Total entries: 1506
# Entries per file: 100
# Number of files to create: 16
# Created data/data-1.json with 100 entries (IDs 1-100)
# ...
# Created index file: data/index.json
```

### Advanced Patterns - Analyzing Data Quality

```python
# Run data quality analysis
python3 analyze_data.py

# Output includes:
# - Field completeness percentages
# - Top 20 positions, crimes, and tags
# - Sample entries with missing data
# - Description length analysis
```

### Advanced Patterns - Searching the Database

```javascript
// Example: The search implementation with debouncing
const debouncedApplyFilters = debounce(applyFilters, 300);
document.getElementById('searchBar').addEventListener('input', debouncedApplyFilters);

// Search filters across multiple fields:
// - name, description, crime, position, tags
const matchesSearch = !searchTerm ||
    entry.name?.toLowerCase().includes(searchTerm) ||
    entry.description?.toLowerCase().includes(searchTerm) ||
    entry.crime?.some(c => c.toLowerCase().includes(searchTerm)) ||
    entry.position?.some(p => p.toLowerCase().includes(searchTerm)) ||
    entry.tags?.some(t => t.toLowerCase().includes(searchTerm));
```

## Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.x | Running utility scripts and http.server |
| Modern Web Browser | N/A | Chrome, Firefox, Safari, Edge for viewing application |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python Standard Library | 3.x | json, os, math, collections modules for data processing |

No external npm packages, pip packages, or third-party JavaScript libraries are required. The application is completely self-contained using vanilla JavaScript and Python standard library.

## Integration Points

### Works With

Standalone project - no direct Mnehmos integrations. This research database operates independently and does not integrate with other Mnehmos projects.

### External Services

| Service | Purpose | Required |
|---------|---------|----------|
| Web Browser | Rendering the single-page application | Yes |
| HTTP Server | Serving static files (Python, Node.js, or PHP) | Yes |
| Source URLs | External news articles and court records linked in database | No (for offline viewing) |

## Development Guide

### Prerequisites

- Python 3.x (for running utility scripts and local server)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Git (for version control)
- Text editor (for editing JSON data or HTML/CSS/JavaScript)

### Setup

```bash
# Clone the repository
git clone https://github.com/Mnehmos/mnehmos.right-wing-predators.research
cd mnehmos.right-wing-predators.research

# No installation needed - uses Python standard library and vanilla JavaScript
# Data files are already included in repository

# Optional: Make serve script executable (Unix/Mac)
chmod +x serve.sh
```

### Running Locally

```bash
# Development mode - Python HTTP server
python3 -m http.server 8000
# Or use the convenience script:
./serve.sh

# Alternative: Node.js http-server
npm install -g http-server
http-server -p 8000

# Alternative: PHP built-in server
php -S 127.0.0.1:8000

# Then open: http://127.0.0.1:8000/
```

### Testing

```bash
# Run data analysis to verify data integrity
python3 analyze_data.py

# Verify split files are up to date
python3 split_data.py

# Check for entries needing research
python3 identify_research_needed.py

# Manual testing: Open browser and verify:
# - Search functionality with 300ms debouncing
# - Filter by crime, position, tag, year
# - Sort by ID, name, year (ascending/descending)
# - Pagination (10, 25, 50, 100, all per page)
# - CSV export with current filters
# - Mobile responsiveness
```

### Building

```bash
# No build step required - static HTML/CSS/JavaScript
# To regenerate split data files after editing data.json:
python3 split_data.py

# Output location: data/ directory
# Files created: data/data-1.json through data/data-16.json, data/index.json
```

## Maintenance Notes

### Known Issues

1. Data loading requires CORS-compatible HTTP server (cannot use file:// protocol due to browser security restrictions)
2. Some entries have incomplete data (missing year, crime type, or detailed descriptions)
3. Manual enrichments in manual_enrichments.json need to be periodically applied with apply_enrichments.py
4. CSV export includes all filtered results which may be large (1,506 entries max)

### Future Considerations

1. Implement server-side search for better performance with larger datasets
2. Add advanced analytics dashboard showing trends over time
3. Create automated web scraping to keep sources updated
4. Add data validation schema to ensure consistency
5. Implement full-text search with better relevance ranking
6. Add ability to contribute new entries via GitHub issues or pull requests
7. Create API endpoint for programmatic access to database

### Code Quality

| Metric | Status |
|--------|--------|
| Tests | None (manual browser testing only) |
| Linting | None (vanilla JavaScript, Python scripts) |
| Type Safety | None (vanilla JavaScript, Python without type hints) |
| Documentation | README only with inline HTML/JavaScript/Python comments |

---

## Appendix: File Structure

```
mnehmos.right-wing-predators.research/
├── data/
│   ├── data-1.json           # Entries 1-100
│   ├── data-2.json           # Entries 101-200
│   ├── ...                   # Additional data chunks
│   ├── data-16.json          # Entries 1501-1506
│   └── index.json            # Manifest listing all data files
├── analyze_data.py           # Python script for data quality analysis
├── apply_enrichments.py      # Python script to apply manual corrections
├── auto_cleanup.py           # Python script for automated cleanup
├── data.json                 # Original monolithic JSON file (backup)
├── identify_research_needed.py # Script to identify incomplete entries
├── index.html                # Main single-page web application
├── manual_enrichments.json   # Manual data corrections and enrichments
├── README.md                 # Project documentation
├── serve.bat                 # Windows batch script to start server
├── serve.sh                  # Unix/Mac shell script to start server
├── split_data.py             # Python script to split data.json into chunks
└── PROJECT_KNOWLEDGE.md      # This document
```

---

*Generated by Project Review Orchestrator | 2025-12-29*
*Source: https://github.com/Mnehmos/mnehmos.right-wing-predators.research*
