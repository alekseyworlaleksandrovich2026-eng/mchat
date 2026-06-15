---
name: csv-json-to-table
description: "Convert CSV or JSON data into a formatted Markdown table and save it."
type: tool
---

When a user provides CSV or JSON text, parse it and generate a Markdown table. For CSV, assume first row as headers; for JSON, assume array of objects (use keys as headers). Output the Markdown table in a code block and save it as output.md file.

Example usage:
User: "Convert this CSV:\nName,Age\nAlice,30\nBob,25"
Assistant should execute the skill and produce a table.