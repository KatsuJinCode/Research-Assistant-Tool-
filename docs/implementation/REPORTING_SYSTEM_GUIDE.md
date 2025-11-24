# Comprehensive Export and Reporting System

## Overview

The Research Assistant Tool now includes a comprehensive export and reporting system that allows users to generate professional reports, export data in multiple formats, create custom templates, and schedule automated exports.

## Features

### 1. PDF Report Generation ✅

Generate professional PDF reports with complete research analysis.

**Features:**
- 📊 **Title Page** - Branded title page with project overview
- 📑 **Table of Contents** - Navigable section index
- 📈 **Graph Summary** - Complete statistics and metrics
- 📄 **Document List** - All analyzed documents with metadata
- 🎯 **Claim Analysis** - Extracted claims sorted by confidence
- 🔍 **Evidence Quality Metrics** - Evidence distribution and quality indicators
- 📸 **Visual Graph Snapshot** - Current graph visualization embedded
- 📄 **Page Numbers & Headers** - Professional formatting throughout

**Usage:**
1. Click the "📄 Reports" button in the header
2. Select "PDF Report" from the Export tab
3. Configure export options (optional)
4. Click "Generate PDF"
5. PDF downloads automatically

**Technical Details:**
- Uses jsPDF library for PDF generation
- Captures live graph visualization as image
- Fetches data from backend API endpoint
- Supports custom branding and colors

### 2. Markdown Export ✅

Export research data in markdown format for documentation.

**Features:**
- 📝 Hierarchical structure (documents → claims → evidence)
- 🔗 Links between related items
- 📊 Metadata tables with statistics
- 💻 Code blocks for technical content
- 🎯 Full project or selected nodes export

**Output Format:**
```markdown
# Project Name

**Generated:** [timestamp]

## Overview
| Metric | Count |
|--------|-------|
| Total Documents | X |
| Total Claims | Y |

## Documents
### 1. Document Title
- **ID:** `doc_id`
- **Created:** [date]

## Claims
### Claim 1
[Claim text]
- **Confidence:** X%
- **ID:** `claim_id`

## Evidence Network
[Evidence relationships]
```

**Usage:**
1. Click "📄 Reports" → "Markdown"
2. Downloads .md file with timestamp
3. Ready for GitHub, GitLab, or documentation systems

### 3. BibTeX Citation Integration ✅

Generate BibTeX entries for all documents and references.

**Features:**
- 📚 Auto-detect citation format from metadata
- 📖 Support for common entry types:
  - `@article` - Journal articles
  - `@book` - Books
  - `@inproceedings` - Conference papers
  - `@techreport` - Technical reports
  - `@phdthesis` - Dissertations
  - `@misc` - Other sources
- 🔑 Generate unique citation keys
- 📋 Export complete .bib file
- 📄 Copy individual citations to clipboard

**Output Format:**
```bibtex
@article{author2025title,
  title = {Document Title},
  author = {Author Name},
  year = {2025},
  journal = {Journal Name},
  doi = {10.xxxx/xxxxx},
  note = {Analyzed with Research Assistant Tool on 2025-01-15}
}
```

**Usage:**
1. Click "📄 Reports" → "BibTeX Citations"
2. Downloads .bib file compatible with LaTeX, Zotero, Mendeley
3. Import into reference manager

**Citation Key Format:**
- `{first_author_lastname}{year}{first_title_word}`
- Example: `smith2025artificial`

### 4. Custom Report Templates ✅

Create and manage custom report templates using Handlebars.js.

**Default Templates (5 included):**

1. **Executive Summary**
   - High-level overview for stakeholders
   - Key statistics and findings
   - Concise 1-page format

2. **Technical Report**
   - Detailed technical analysis
   - Full methodology section
   - Complete results and conclusion

3. **Literature Review**
   - Academic format
   - Source bibliography
   - Thematic analysis

4. **Quick Summary**
   - Brief one-page summary
   - Top claims only
   - Fast generation

5. **Evidence Report**
   - Focus on evidence quality
   - Network analysis
   - Quality metrics

**Creating Custom Templates:**

1. Click "📄 Reports" → "Templates" tab
2. Click "➕ Create Custom Template"
3. Enter template details:
   - Name
   - Description
   - Template content (Handlebars syntax)
4. Click "Save Template"

**Available Variables:**
```handlebars
{{project_name}}           - Project name
{{project_description}}    - Project description
{{date}}                   - Generation date
{{document_count}}         - Number of documents
{{claim_count}}            - Number of claims
{{avg_confidence}}         - Average confidence %
{{relationship_count}}     - Total relationships

{{#each documents}}        - Iterate over documents
  {{this.title}}
  {{this.metadata}}
{{/each}}

{{#each claims}}           - Iterate over claims
  {{this.text}}
  {{this.confidence}}
{{/each}}

{{#each top_claims}}       - Top 5 claims
{{/each}}

{{supporting_count}}       - Supporting evidence count
{{contradicting_count}}    - Contradicting evidence count
{{evidence_per_claim}}     - Average evidence per claim
{{network_density}}        - Network density metric
```

**Template Example:**
```handlebars
# {{project_name}} - Custom Report

Generated: {{date}}

## Statistics
- Documents: {{document_count}}
- Claims: {{claim_count}}
- Confidence: {{avg_confidence}}%

## Top Findings
{{#each top_claims}}
{{@index}}. {{this.text}} ({{this.confidence}}%)
{{/each}}

## Conclusion
Analysis complete with {{relationship_count}} relationships identified.
```

**Template Storage:**
- Saved in browser localStorage
- Persists across sessions
- Export/import templates (planned)

### 5. Scheduled Exports ✅

Automate report generation on a schedule using cron expressions or intervals.

**Schedule Types:**

1. **Interval-Based**
   - Every X hours/days
   - Example: Every 24 hours

2. **Cron Expression**
   - Advanced scheduling
   - Examples:
     - `0 0 * * *` - Daily at midnight
     - `0 0 * * 0` - Weekly on Sunday
     - `0 0 1 * *` - Monthly on 1st
     - `0 9 * * 1-5` - Weekdays at 9am

3. **Pre-set Options**
   - Daily
   - Weekly
   - Monthly

**Configuration Options:**
- Export format (PDF, Markdown, BibTeX)
- Schedule type and timing
- Export destination path
- Email delivery (if configured)

**Usage:**

1. Click "📄 Reports" → "Schedule" tab
2. Configure schedule:
   ```
   Export Format: PDF Report
   Schedule Type: Daily
   Interval: 24 hours
   Export Path: /path/to/reports (optional)
   Email: your@email.com (optional)
   ```
3. Click "Create Schedule"
4. View active schedules
5. Cancel/modify as needed

**Backend Integration:**
- Uses workflow scheduler system
- Background job execution
- Email delivery via SMTP (if configured)
- Export to specified directory
- History tracking

## API Endpoints

### POST /api/reports/generate

Generate report data.

**Request:**
```json
{
  "project_id": "optional_project_id",
  "include_documents": true,
  "include_claims": true,
  "include_evidence": true,
  "include_statistics": true
}
```

**Response:**
```json
{
  "project": {
    "id": "project_id",
    "name": "Project Name",
    "description": "...",
    "created_at": "2025-01-15T10:30:00Z"
  },
  "statistics": {
    "total_documents": 10,
    "total_claims": 50,
    "total_evidence": 80,
    "total_relationships": 120,
    "avg_confidence": 0.75
  },
  "documents": [...],
  "claims": [...],
  "evidence": [...],
  "generated_at": "2025-01-15T10:30:00Z"
}
```

### POST /api/reports/schedule

Schedule automatic report generation.

**Request:**
```json
{
  "schedule_type": "cron",
  "schedule_config": {
    "expression": "0 0 * * *"
  },
  "export_format": "pdf",
  "project_id": "optional_project_id",
  "email": "optional@email.com",
  "export_path": "/optional/path"
}
```

**Response:**
```json
{
  "schedule_id": "uuid",
  "message": "Report scheduled successfully",
  "schedule": {...}
}
```

### GET /api/reports/schedules

List all scheduled reports.

**Response:**
```json
[
  {
    "schedule_id": "uuid",
    "schedule_type": "cron",
    "schedule_config": {...},
    "created_at": "2025-01-15T10:30:00Z",
    "enabled": true
  }
]
```

### DELETE /api/reports/schedule/<schedule_id>

Cancel a scheduled report.

**Response:**
```json
{
  "message": "Schedule cancelled successfully"
}
```

## File Structure

```
web_ui/
├── static/js/
│   ├── report-generator.js      # Core report generation logic
│   └── report-modal.js           # UI modal and interactions
├── report_routes.py              # Backend API endpoints
└── templates/
    └── index.html                # Updated with Reports button

backend/
└── workflows/
    └── scheduler.py              # Workflow scheduler integration
```

## Dependencies

### JavaScript Libraries (CDN)
- **jsPDF 2.5.1** - PDF generation
  ```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
  ```

- **Handlebars.js 4.7.8** - Template engine
  ```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/handlebars.js/4.7.8/handlebars.min.js"></script>
  ```

### Python Packages
- Flask (existing)
- Backend database repositories (existing)
- Workflow scheduler (existing)

## Browser Compatibility

✅ **Chrome/Edge** - Full support
✅ **Firefox** - Full support
✅ **Safari** - Full support
⚠️ **IE11** - Not supported (modern ES6 features used)

## Performance Considerations

- **Large Graphs**: PDF generation may take 5-10 seconds for graphs with 1000+ nodes
- **Graph Snapshots**: Uses HTML5 Canvas for rendering, may be memory intensive
- **Template Processing**: Handlebars compilation is fast but cached for better performance
- **Scheduled Exports**: Background jobs don't block UI

## Troubleshooting

### Issue: "jsPDF library not loaded"
**Solution:** Ensure CDN scripts are loading. Check browser console for errors.

### Issue: PDF generation fails
**Solution:**
1. Check browser console for errors
2. Ensure graph is rendered before generating PDF
3. Try without graph snapshot option

### Issue: Template variables not substituting
**Solution:**
1. Verify Handlebars.js is loaded
2. Check variable names match exactly (case-sensitive)
3. Use browser console to debug template data

### Issue: Scheduled export not running
**Solution:**
1. Check backend logs for errors
2. Verify workflow scheduler is running
3. Check schedule configuration

## Export Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| includeGraphSnapshot | boolean | true | Include visual graph in PDF |
| includeDocuments | boolean | true | Include document list |
| includeClaims | boolean | true | Include claim analysis |
| includeEvidence | boolean | true | Include evidence metrics |
| includeStatistics | boolean | true | Include statistics |
| projectId | string | current | Project to export |

## Report History

All generated reports are tracked in localStorage:

```javascript
{
  id: "timestamp",
  type: "pdf|markdown|bibtex|template",
  filename: "report-2025-01-15.pdf",
  timestamp: "2025-01-15T10:30:00Z",
  project_name: "Project Name",
  document_count: 10,
  claim_count: 50
}
```

Access history via "📄 Reports" → "History" tab.

History is limited to last 50 reports to prevent localStorage bloat.

## Future Enhancements

- [ ] Excel/CSV export
- [ ] PowerPoint presentation generation
- [ ] Email report templates (HTML)
- [ ] Report comparison (diff between runs)
- [ ] Template marketplace
- [ ] Cloud storage integration (Dropbox, Google Drive)
- [ ] Advanced scheduling (conditional triggers)
- [ ] Report versioning
- [ ] Collaborative report editing
- [ ] Custom branding (logos, colors)

## Examples

### Example 1: Weekly PDF Reports

```javascript
// Schedule weekly PDF reports every Monday at 9am
ReportGenerator.scheduleExport({
  schedule_type: 'cron',
  schedule_config: {
    expression: '0 9 * * 1'
  },
  export_format: 'pdf',
  email: 'team@example.com',
  project_id: 'my_project'
});
```

### Example 2: Custom Executive Summary

```javascript
// Create custom executive summary template
const template = {
  name: 'My Executive Summary',
  description: 'Custom format for executives',
  template: `
# Executive Summary: {{project_name}}

## Key Metrics
- **Documents Analyzed:** {{document_count}}
- **Claims Extracted:** {{claim_count}}
- **Confidence Level:** {{avg_confidence}}%

## Top 3 Findings
{{#each top_claims}}
{{@index}}. {{this.text}}
{{/each}}

Generated on {{date}}
  `,
  custom: true,
  sections: ['overview', 'top_claims']
};

ReportGenerator.saveTemplate('my_executive_summary', template);
```

### Example 3: Export All Formats

```javascript
// Export in all formats at once
async function exportAll() {
  await ReportGenerator.generatePDFReport();
  await ReportGenerator.exportMarkdown();
  await ReportGenerator.exportBibTeX();
  console.log('All exports complete!');
}
```

## Integration with Other Features

### Graph Visualization
Reports automatically capture the current graph visualization state.

### Document Processor
Reports include all processed documents with full metadata.

### Claim Extraction
All extracted claims are included with confidence scores.

### Evidence Network
Complete evidence network is analyzed for quality metrics.

### Project System
Reports are project-aware and filter data by active project.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl/Cmd + E | Open Reports modal |
| Ctrl/Cmd + Shift + P | Quick PDF export |
| Ctrl/Cmd + Shift + M | Quick Markdown export |
| Esc | Close Reports modal |

*(Shortcuts to be implemented)*

## Accessibility

- ✅ Keyboard navigation support
- ✅ ARIA labels for screen readers
- ✅ High contrast mode compatible
- ✅ Responsive design for mobile

## License

Part of the Research Assistant Tool.
See main LICENSE file for details.

## Support

For issues, questions, or feature requests:
1. Check this documentation
2. Review browser console for errors
3. Check GitHub Issues
4. Contact development team

---

**Version:** 1.0.0
**Last Updated:** January 15, 2025
**Author:** Research Assistant Tool Development Team
