# SIP AI Agent Dashboard Frontend

This package contains the React + TypeScript dashboard that powers the SIP AI Agent monitoring UI.  It is built with Vite and Tailwind CSS and communicates with the FastAPI backend via REST endpoints and the `/ws/events` WebSocket.

## Getting started

```bash
cd web
npm install
npm run dev
```

The dev server runs on port 5173.  Configure the backend to allow cross-origin requests or proxy requests during development if you need live data.  The production build uses relative paths and is served by the FastAPI application on port 8080.

## Building for production

```bash
npm run build
```

The build output is written to `../app/static/dashboard`.  The Docker image and the local FastAPI server automatically serve any files in that directory at `/dashboard`.

## Linting

```bash
npm run lint
```

## Testing

```bash
npm run test
```

Vitest runs in a headless jsdom environment, making the suite suitable for local development and continuous integration.

## Folder structure

- `src/` – React application code
- `src/components/` – UI components for status, calls, logs, history, configuration editor, theming and error states
- `src/hooks/` – data-fetching and theme hooks that integrate with backend APIs and WebSocket streams
- `src/utils/` – helper utilities for formatting durations and timestamps

Tailwind configuration lives in `tailwind.config.js` and global styles are in `src/index.css`.
