# Local data cleaning and quality checks

The source Google Sheet is read-only. Keep the acquired CSV or SDK snapshot unchanged; normalize values only in the local analysis layer. Multi-select analysis trims whitespace, removes empty fragments and duplicate choices, maps PET aliases to `PET (Cambridge)`, and matches known options without splitting the comma-containing Q31 label.

`survey-report generate` reads the configured schema and writes a local `report/quality.json` alongside the report. The audit flags missing or duplicate headers, categories and multi-select fragments outside the known schema, and Q11–Q27 values that are not numeric levels 1–5. Free-text Q32 responses are excluded from the audit output. The quality file is Git-ignored because unknown source values should stay local until reviewed.

Run with the current source schema:

```powershell
uv run --locked survey-report generate --csv $env:TEMP\survey.csv --config config/survey.english_certs.local.toml --out report --date YYYY-MM-DD
```

Review `report/quality.json` before interpreting results. Add an alias or valid category to the example configuration only after checking it against the source form; do not silently treat an unknown value as valid. No cleaning step writes back to the Google Sheet.
