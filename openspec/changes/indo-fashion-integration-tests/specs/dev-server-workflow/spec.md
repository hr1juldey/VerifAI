## ADDED Requirements

### Requirement: FastAPI hot reload with watchfiles
The dev server SHALL run with `uvicorn --reload --reload-dir app/` using watchfiles for file change detection. Only the `app/` directory SHALL be watched for changes.

#### Scenario: Code change triggers reload
- **WHEN** a Python file in `app/` is modified while the dev server is running
- **THEN** uvicorn SHALL detect the change via watchfiles and reload the application within 2 seconds

#### Scenario: Test file change does not trigger reload
- **WHEN** a file in `tests/` is modified while the dev server is running
- **THEN** uvicorn SHALL NOT reload the application

### Requirement: Structured logging to file
The application SHALL log to `verifai.log` in the repository root via a JSON log config file. The log config SHALL output structured log entries with timestamp, level, logger name, and message. Logs SHALL also appear in console with colors.

#### Scenario: Application writes to log file
- **WHEN** the FastAPI app starts and a request is made
- **THEN** log entries SHALL appear in `verifai.log` with timestamp, level, and message

#### Scenario: Log file path is configurable
- **WHEN** the `LOG_CONFIG_PATH` environment variable is set to a custom path
- **THEN** uvicorn SHALL use that log config instead of the default `log_config.json`

### Requirement: Dev server startup script
The project SHALL provide `scripts/dev.sh` that creates a tmux session named `verifai` with two panes: pane 0 running the FastAPI dev server with hot reload, pane 1 as an interactive bash shell for running tests.

#### Scenario: Start dev session
- **WHEN** `scripts/dev.sh` is executed
- **THEN** a tmux session named `verifai` SHALL be created with the server running in pane 0 and a bash shell in pane 1

#### Scenario: Server logs visible in tmux
- **WHEN** the tmux session is attached
- **THEN** pane 0 SHALL show uvicorn startup output and subsequent request logs

#### Scenario: Clean shutdown
- **WHEN** the tmux session is killed
- **THEN** the uvicorn process SHALL be terminated cleanly

### Requirement: verifai.log in gitignore
The `verifai.log` file SHALL be listed in `.gitignore` to prevent log files from being committed.

#### Scenario: Log file not tracked
- **WHEN** `git status` is run after the server has written to `verifai.log`
- **THEN** `verifai.log` SHALL NOT appear in untracked files
