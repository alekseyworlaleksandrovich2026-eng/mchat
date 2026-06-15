# Changelog — patent-search

## 1.0.11

- Fix patent search sort: send 9235 API parameter `s` (was incorrectly `sort`, so all results defaulted to relevance).
- Add `query_utils.py` to dist bundle; map action-pill phrases like「按最新公开排序」to `!documentDate`.
- Search result table shows separate 申请日 / 公开日 columns and current sort label.

## 1.0.10

- Streamlined codebase: removed 8 scripts (trend, analysis, test, config) for a lighter core.
- Added Excel export capability via new `excel_export.py`.
- Introduced `export_deps.py` for export-related dependencies.
- Added `.gitignore` and LICENSE for improved project structure and clarity.
- Updated documentation with a more concise, tabular overview, usage examples, configuration, and troubleshooting.
- Clarified required credentials and configuration methods for 9235 API integration.

## 1.0.0

- Initial release: search, detail, claims, description, legal events, citations, similar patents, company portrait, analytics.
