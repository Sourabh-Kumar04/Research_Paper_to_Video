# Advanced Video Template Engine

A sophisticated video template engine that enables users to create reusable video templates with dynamic content insertion, multi-format output generation, and interactive elements.

## Features

- **Dynamic Templates**: Create reusable templates with content slots for different media types
- **Interactive Elements**: Support for chapters, annotations, hotspots, and clickable elements
- **Multi-Format Output**: Generate MP4, WebM, MOV in various quality presets simultaneously
- **Advanced Animations**: Keyframe-based animations that adapt to dynamic content
- **Collaboration**: Template sharing, version control, and collaborative editing
- **Professional Features**: Batch processing, caching, distributed rendering, and quality validation

## Architecture

The system follows a microservices architecture with the following services:

- **Template Service**: Template CRUD operations and version control
- **Content Service**: Content validation and processing
- **Rendering Service**: Video generation pipeline orchestration
- **Queue Service**: Job queuing and distributed processing
- **Export Service**: Multi-format output generation
- **Interactive Service**: Interactive elements and metadata processing

## Prerequisites

- Node.js 18+ and npm
- MongoDB 5.0+
- Redis 6.0+
- FFmpeg 4.4+

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd video-template-engine
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start the development server:
```bash
npm run dev
```

## Development

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build the TypeScript project
- `npm test` - Run tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues

### Project Structure

```
src/
├── config/          # Configuration files
├── services/        # Microservices implementation
├── types/           # TypeScript type definitions
├── utils/           # Utility functions
├── test/            # Test setup and utilities
└── index.ts         # Application entry point
```

## API Documentation

### Health Check
```
GET /health
```

### Templates API
```
POST /api/v1/templates          # Create template
GET /api/v1/templates           # List templates
GET /api/v1/templates/:id       # Get template
PUT /api/v1/templates/:id       # Update template
DELETE /api/v1/templates/:id    # Delete template
```

### Content API
```
POST /api/v1/content/validate   # Validate content
POST /api/v1/content/process    # Process content
POST /api/v1/content/batch      # Batch process content
```

### Rendering API
```
POST /api/v1/render             # Start render job
GET /api/v1/render/:jobId       # Get render status
DELETE /api/v1/render/:jobId    # Cancel render job
```

## Testing

The project uses Jest for unit testing and fast-check for property-based testing:

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Property-Based Testing

Property-based tests validate universal properties across all inputs:

- Template structure validation
- Content compatibility checking
- Multi-format output consistency
- Animation adaptation
- Batch processing reliability

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.