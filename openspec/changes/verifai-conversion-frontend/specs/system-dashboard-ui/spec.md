## ADDED Requirements

### Requirement: System health display
The dashboard SHALL fetch and display system health from `GET /health`.

#### Scenario: Health status loaded
- **WHEN** user navigates to `/dashboard`
- **THEN** the system SHALL fetch `/health` and display status, GPU availability, model loaded state, cache size, Ollama provider, and Ollama connectivity

#### Scenario: Health fetch failure
- **WHEN** the `/health` endpoint is unreachable
- **THEN** the system SHALL display "Backend unavailable" with a red status indicator

### Requirement: Health status indicators
The dashboard SHALL use Warehouse Dark color-coded indicators for each health metric.

#### Scenario: All systems healthy
- **WHEN** `status` is "ok", `gpu_available` is true, `model_loaded` is true, and `ollama_connected` is true
- **THEN** each metric SHALL display a green (#4ade80) indicator dot with "Available" or "Connected"

#### Scenario: Degraded state
- **WHEN** any metric indicates failure
- **THEN** the corresponding metric SHALL display a red (#f87171) indicator dot with "Unavailable" or "Disconnected"

### Requirement: Calibration statistics display
The dashboard SHALL fetch and display calibration statistics from `GET /calibration/stats`.

#### Scenario: Calibration stats available
- **WHEN** calibration data exists
- **THEN** the system SHALL display a table with categories, Type 1 error rate, Type 2 error rate, and total count per category

#### Scenario: No calibration data
- **WHEN** the response contains `status: "no_data"`
- **THEN** the system SHALL display "No calibration data recorded yet"

### Requirement: Auto-refresh health
The dashboard SHALL periodically refresh health status.

#### Scenario: Automatic health refresh
- **WHEN** the dashboard page is active
- **THEN** the system SHALL re-fetch `/health` every 30 seconds and update the display

**NOTE: This capability is DEFERRED. The spec is written for completeness but implementation will occur in a later change.**
