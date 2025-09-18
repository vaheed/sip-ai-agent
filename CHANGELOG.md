# Changelog

All notable changes to this project will be documented in this file.  Dates
are given in UTC.

## [2.1.0] – 2025‑08‑31

### Added

* **Configuration dashboard.**  The monitoring UI now includes a `/dashboard`
  endpoint with a configuration editor, call history table and live logs.  You
  can update your `.env` values from the browser and restart the container to
  apply them.
* **Call history.**  Active calls are tracked along with start and end times,
  and displayed with duration in the dashboard.
* **Editable environment.**  The dashboard writes changes back to the `.env`
  file so you no longer need to manually edit it.
* **Improved documentation.**  Added step‑by‑step integration guides for
  FreePBX and VICIdial, clarified realtime API usage and elaborated on
  dashboard functionality.  Added this `CHANGELOG.md` and a
  `CONTRIBUTING.md` with contribution guidelines.

### Changed

* **Monitor code refactoring.**  Factored out `load_config` and `save_config`
  helpers to read and persist the `.env` file.  Added imports for
  `request` and improved error handling.
* **Project structure.**  The project is now packaged as a complete Git
  repository with top‑level README, CONTRIBUTING and CHANGELOG files.

## [2.0.0] – 2024

### Added

* **Realtime API support.**  Added `OPENAI_MODE` environment variable to
  switch between the legacy `/v1/audio/speech` API and OpenAI’s new
  realtime API.  The realtime API streams audio in both directions and
  eliminates the latency associated with converting speech to text and back
  again.  Support for new voices like Cedar and Marin was added to provide
  more natural call experiences, in line with the [OpenAI realtime API
  guide](https://platform.openai.com/docs/guides/realtime_api).
* **Asynchronous audio handling.**  Refactored the agent to use
  `asyncio` for WebSocket and audio streaming, improving performance.
* **Monitoring server.**  Added a simple Flask monitor to display SIP
  registration state, active calls, token usage and logs.

## [1.x] – 2023

Initial releases of the SIP AI agent with support for the legacy speech API,
Dockerisation and basic logging.

---

For older history and details, see the commit log.