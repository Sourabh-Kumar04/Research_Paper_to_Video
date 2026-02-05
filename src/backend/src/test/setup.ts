import { DatabaseConfig } from '../config/database';

// Test setup configuration
beforeAll(async () => {
  // Set test environment
  process.env.NODE_ENV = 'test';
  process.env.MONGODB_URI = 'mongodb://localhost:27017/video-template-engine-test';
  process.env.REDIS_URL = 'redis://localhost:6379/1';
  
  // Initialize test database connections
  const dbConfig = DatabaseConfig.getInstance();
  await dbConfig.connectMongoDB();
  await dbConfig.connectRedis();
});

afterAll(async () => {
  // Clean up database connections
  const dbConfig = DatabaseConfig.getInstance();
  await dbConfig.disconnect();
});

// Global test utilities
global.testTimeout = 30000;

// Mock external services for testing
jest.mock('fluent-ffmpeg', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    input: jest.fn().mockReturnThis(),
    output: jest.fn().mockReturnThis(),
    on: jest.fn().mockReturnThis(),
    run: jest.fn()
  }))
}));

// Property-based testing utilities
export const generateRandomString = (length: number = 10): string => {
  return Math.random().toString(36).substring(2, length + 2);
};

export const generateRandomNumber = (min: number = 0, max: number = 100): number => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

export const generateRandomResolution = () => ({
  width: generateRandomNumber(640, 3840),
  height: generateRandomNumber(480, 2160)
});

export const generateRandomPosition = () => ({
  x: generateRandomNumber(0, 1920),
  y: generateRandomNumber(0, 1080)
});

export const generateRandomDimensions = () => ({
  width: generateRandomNumber(100, 800),
  height: generateRandomNumber(100, 600)
});