# Changelog

## 1.2.1

- Make snow-removal sensors and the snow-event binary sensor coordinator-aware so successful refreshes update entity states and attributes.
- Add regression tests for coordinator-backed sensor and binary-sensor entities.
- Remove accidentally committed Python bytecode and ignore Python cache and virtual-environment files.

## 1.2.0

- Keep the last successful coordinator data when a GIS layer request fails instead of presenting failed layers as zero activity.
- Improve snow status parsing to avoid false active/completed matches.
- Support abbreviated month names in the City's page update date.
- Record the timestamp of the last successful data refresh.
- Close the HTTP session on unload and failed initial setup.
- Prevent duplicate config entries and reload after polling interval changes.
- Add parser regression tests and GitHub Actions test coverage.

## 1.1.0

- Previous release.
