# Read reports in the browser

Add a project-relative HTML, Markdown or PDF path to `overview.json` under `links`. The file card opens a read-only browser page. Markdown headings, lists, tables, quotes and code blocks become HTML while the source file stays intact. `/files/<path>` keeps the original download.

The reader follows explicit HTML, Markdown and CSS references to existing project files. Each dependency receives a scoped URL tied to its full path, so two files sharing a basename remain distinct. Links to another listed report use that report's own scope. Refreshing a report picks up edited references.

The existing direct-loopback checks apply before reading. Report scopes allow GET and HEAD; project-external files, symbolic links, discussion attachments and private attachments stay outside the scope. Report scripts and network requests are disabled. This reader serves the existing local, single-user installation; external hosting uses its own reviewed authentication and deployment design.

Example:

```json
{"links": [{"title": "Cache comparison", "path": "reports/cache.html"}]}
```

Place a linked table or figure inside the project and reference its relative path from the report. Use the report kit for new result pages and keep operational logs in a companion file.
