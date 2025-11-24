# Reporting System - Quick Reference Card

## 🚀 Quick Start

1. Click **📄 Reports** button in header
2. Choose export type
3. Configure options (optional)
4. Click export button
5. File downloads automatically!

---

## 📄 Export Formats

| Format | Use Case | Button |
|--------|----------|--------|
| **PDF** | Professional reports | 📕 PDF Report |
| **Markdown** | Documentation, GitHub | 📝 Markdown |
| **BibTeX** | LaTeX, reference managers | 📚 BibTeX Citations |
| **JSON** | Data processing | 💾 JSON Data |

---

## 📋 Default Templates

| Template | Description | Best For |
|----------|-------------|----------|
| **Executive Summary** | High-level overview | Stakeholders |
| **Technical Report** | Detailed analysis | Technical teams |
| **Literature Review** | Academic format | Research papers |
| **Quick Summary** | One-page brief | Quick updates |
| **Evidence Report** | Evidence focus | Quality analysis |

---

## ⏰ Schedule Types

| Type | Example | Use Case |
|------|---------|----------|
| **Interval** | Every 24 hours | Regular updates |
| **Daily** | Every day at midnight | Daily reports |
| **Weekly** | Every Monday | Weekly summaries |
| **Monthly** | 1st of each month | Monthly reviews |
| **Cron** | `0 9 * * 1-5` | Custom schedules |

---

## 🔧 Common Cron Expressions

| Expression | Meaning |
|------------|---------|
| `0 0 * * *` | Daily at midnight |
| `0 9 * * 1-5` | Weekdays at 9am |
| `0 0 * * 0` | Weekly on Sunday |
| `0 0 1 * *` | Monthly on 1st |
| `0 */6 * * *` | Every 6 hours |

---

## 📊 Export Options

- ☑️ **Include graph snapshot** - Visual graph image in PDF
- ☑️ **Include documents** - Document list with metadata
- ☑️ **Include claims** - All extracted claims
- ☑️ **Include evidence** - Evidence metrics and relationships

---

## 🎯 Template Variables

### Basic Variables
```handlebars
{{project_name}}          Project name
{{date}}                  Current date/time
{{document_count}}        Number of documents
{{claim_count}}           Number of claims
{{avg_confidence}}        Average confidence (%)
{{relationship_count}}    Total relationships
```

### Loop Variables
```handlebars
{{#each documents}}       Loop through documents
  {{this.title}}          Document title
  {{this.created_at}}     Creation date
{{/each}}

{{#each claims}}          Loop through claims
  {{this.text}}           Claim text
  {{this.confidence}}     Confidence score
{{/each}}

{{#each top_claims}}      Top 5 claims only
{{/each}}
```

### Evidence Variables
```handlebars
{{supporting_count}}      Supporting evidence count
{{contradicting_count}}   Contradicting evidence count
{{evidence_per_claim}}    Avg evidence per claim
{{network_density}}       Network density %
```

---

## 🎨 UI Navigation

### Tabs
1. **Export** - Quick export buttons
2. **Templates** - Manage templates
3. **Schedule** - Configure schedules
4. **History** - View past reports

### Buttons
- **Generate PDF** - Create PDF report
- **Export Markdown** - Download .md file
- **Export BibTeX** - Download .bib file
- **Use Template** - Generate from template
- **Create Schedule** - Set up automation

---

## 🔐 API Endpoints

```
POST   /api/reports/generate       Generate report data
POST   /api/reports/schedule       Schedule export
GET    /api/reports/schedules      List schedules
DELETE /api/reports/schedule/:id   Cancel schedule
```

---

## 💡 Tips & Tricks

### Tip 1: Fast PDF Generation
Uncheck "Include graph snapshot" for faster generation (3x speedup)

### Tip 2: Custom Templates
Copy a default template as starting point for customization

### Tip 3: Scheduled Reports
Use interval-based for simplicity, cron for advanced control

### Tip 4: BibTeX Keys
Citation keys format: `{author}{year}{title_word}`

### Tip 5: History Tracking
Check History tab to see all generated reports

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| PDF not generating | Check browser console, try without graph snapshot |
| Template not working | Verify variable names are exact (case-sensitive) |
| Schedule not running | Check backend logs, verify configuration |
| Slow generation | Reduce options, skip graph snapshot |

---

## 📱 Access Reports

### From Header
1. Click **📄 Reports** button
2. Modal opens with all options

### From Code (Advanced)
```javascript
// Generate PDF
await ReportGenerator.generatePDFReport();

// Export Markdown
await ReportGenerator.exportMarkdown();

// Schedule daily report
await ReportGenerator.scheduleExport({
  schedule_type: 'interval',
  schedule_config: { interval_seconds: 86400 },
  export_format: 'pdf'
});
```

---

## 🎓 Learning Resources

- **Full Guide:** `REPORTING_SYSTEM_GUIDE.md`
- **Implementation Details:** `REPORTING_IMPLEMENTATION_SUMMARY.md`
- **Template Examples:** See default templates in UI
- **API Documentation:** See endpoint section above

---

## 🆘 Need Help?

1. Check full documentation: `REPORTING_SYSTEM_GUIDE.md`
2. Review browser console for errors
3. Test with smaller dataset first
4. Contact support team

---

## 📌 Quick Commands

### Generate All Formats
```javascript
// Export everything at once
await ReportGenerator.generatePDFReport();
await ReportGenerator.exportMarkdown();
await ReportGenerator.exportBibTeX();
```

### Create Custom Template
```javascript
const template = {
  name: 'My Report',
  description: 'Custom format',
  template: '# {{project_name}}\n\nDocuments: {{document_count}}',
  custom: true
};
ReportGenerator.saveTemplate('my_report', template);
```

### Schedule Weekly PDF
```javascript
await ReportGenerator.scheduleExport({
  schedule_type: 'cron',
  schedule_config: { expression: '0 9 * * 1' },
  export_format: 'pdf',
  email: 'you@example.com'
});
```

---

## ✅ Success Indicators

- ✅ Green notification: "Report generated successfully"
- ✅ File downloads automatically
- ✅ History updated with new entry
- ✅ No errors in browser console

---

**Version:** 1.0.0
**Last Updated:** January 15, 2025

---

*Print this page for easy reference!*
