# Deprecated/Archived JavaScript Files

This folder contains JavaScript files that have been deprecated or archived to prevent confusion and potential conflicts.

## Files

### property_viewer.js.deprecated
- **Date Moved**: 2025-11-24
- **Reason**: Duplicate implementation of PropertyViewer
- **Details**:
  - This file targets `#detail-panel` and uses methods like `showNodeProperties()`, `renderProperties()`
  - The active version is `property-viewer.js` (hyphen) which targets `#property-viewer-panel` and uses methods like `show()`, `hide()`, `switchTab()`
  - The HTML calls methods from property-viewer.js (hyphen version), so this underscore version was orphaned
  - Both files declaring `const PropertyViewer` caused syntax error: "Identifier 'PropertyViewer' has already been declared"
- **Can be deleted**: Yes, after confirming no issues in production

## Orphaned Files (Not Referenced in HTML)

The following files exist in web_ui/static/js/ but are not referenced in index.html:
- `agent-builder.js` - May be deprecated or dynamically loaded
- `graph-paginator.js` - May be deprecated or dynamically loaded

These should be investigated to determine if they can be moved to trash or if they need to be added to index.html.

## Review Process

To prevent similar issues:
1. Check for files with both hyphen and underscore versions of the same name
2. Verify which version is referenced in HTML
3. Check for orphaned files not referenced anywhere
4. Look for backup files (.bak, .backup, .old, ~)
5. Search for files with similar names using pattern matching
