# Sentinel Vision Frontend

React + TypeScript frontend for the Sentinel Vision security intelligence platform.

## Features

- **Dashboard**: Real-time overview of cameras, threats, and system status
- **Natural Language Search**: Conversational video search interface
- **Threat Management**: View and acknowledge security alerts
- **Camera Monitoring**: Real-time camera status and configuration
- **Person Tracking**: Live view of tracked individuals across cameras

## Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and optimized builds
- **TanStack Query** for server state management
- **Tailwind CSS** for styling
- **Axios** for API communication
- **Lucide React** for icons

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at http://localhost:3000

### Build for Production

```bash
npm run build
```

The build artifacts will be in the `dist/` directory.

## Project Structure

```
src/
├── components/        # Reusable UI components
│   └── Layout.tsx    # Main application layout
├── lib/              # Utilities and helpers
│   ├── api.ts        # API client and endpoints
│   └── utils.ts      # Utility functions
├── pages/            # Page components
│   ├── Dashboard.tsx
│   ├── Search.tsx
│   ├── Threats.tsx
│   ├── Cameras.tsx
│   └── Tracking.tsx
├── App.tsx           # Root component with routing
├── main.tsx          # Application entry point
└── index.css         # Global styles
```

## API Integration

The frontend communicates with the backend API at:
- Base URL: `http://localhost:8000/api/v1`
- WebSocket: `ws://localhost:8000/api/v1/ws`

Configure the API URL in `.env`:

```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Development

### Adding New Features

1. Create new components in `src/components/`
2. Add new pages in `src/pages/`
3. Update routing in `src/App.tsx`
4. Add API endpoints in `src/lib/api.ts`

### Styling

This project uses Tailwind CSS with custom utility classes:

- `btn`, `btn-primary`, `btn-secondary` - Button styles
- `card` - Card container
- `badge`, `badge-critical`, `badge-high`, etc. - Status badges

See `src/index.css` for all custom classes.

## WebSocket Real-time Updates

The application supports WebSocket connections for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?subscriptions=threats,tracking');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // Handle real-time updates
};
```

## Docker Deployment

Build and run with Docker:

```bash
docker build -t sentinel-vision-frontend .
docker run -p 3000:3000 sentinel-vision-frontend
```

Or use Docker Compose from the project root:

```bash
docker-compose up frontend
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Write clean, documented code
4. Test thoroughly before committing

## License

Proprietary - All rights reserved
