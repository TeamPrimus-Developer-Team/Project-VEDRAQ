# VEDRAQ synthetic flood scenario

This dataset is deliberately synthetic and is not live government, NDEM, ISRO, or emergency-service data. It models 15 flood-affected communities around Varanasi for a demonstration of changing response plans.

Road segments are a local demo graph. When `OSRM_ENDPOINT` is configured, VEDRAQ requests real OpenStreetMap road geometry; otherwise it visibly labels the local graph fallback. The scenario includes medical isolation (Z01/Z09), water scarcity (Z01/Z09), shelter pressure, communication failure, high population zones, and aerial response when ground access fails.

Inventory contains 35 individually identified assets: 6 ambulances, 8 water tankers, 6 food trucks, 4 medical teams, 5 rescue vehicles, 4 boats, and 2 helicopters. Statuses are AVAILABLE, DEPLOYED, MAINTENANCE, and UNAVAILABLE.
