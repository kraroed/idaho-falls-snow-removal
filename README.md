# Idaho Falls Snow Removal for Home Assistant

Unofficial Home Assistant integration using the official City of Idaho Falls snow-removal webpage and ArcGIS Snow MapServer.

Features: snow event, working/completed zones and streets, Priority 1/2/3 counts, parking-restriction street-segment count, Downtown/Zone A/Zone B sensors, plow method/agency attributes, manual refresh, and configurable 5–120 minute polling.

Install through HACS as a custom repository, category **Integration**, then restart Home Assistant and add **Idaho Falls Snow Removal** from Settings → Devices & services.

Official sources:
- https://idahofallsidaho.gov/378/Snow-Removal
- https://idahofallsidaho.gov/332/Maps
- https://cifgis.idahofalls.gov/arcgis/rest/services/Snow/MapServer

The parking-restriction GIS layer describes ordinance street geometry; its segment count does not itself prove restrictions are currently active. The integration separately reads the City's public snow-removal page.

Replace `kraroed` in `manifest.json` before publishing the repository.
