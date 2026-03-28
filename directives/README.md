# Directives

This folder contains **SOPs (Standard Operating Procedures)** written in Markdown.  
Each directive defines:

- **Goal** – What this workflow achieves
- **Inputs** – What data/config it needs
- **Tools/Scripts** – Which `execution/` scripts to call
- **Outputs** – What it produces
- **Edge Cases** – Known failure modes and how to handle them

## Convention

One file per task type, e.g.:
- `scrape_website.md`
- `generate_report.md`
- `enrich_leads.md`

Directives are **living documents**. Update them when you discover API constraints, better approaches, or common errors. Do **not** delete or overwrite directives without explicit user approval.
