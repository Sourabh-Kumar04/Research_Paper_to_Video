/**
 * API service for cinematic features.
 * Handles all HTTP requests to the cinematic backend endpoints.
 */

import {
  CinematicProfile,
  CinematicSettings,
  VisualDescription,
  SceneAnalysis,
  PreviewResponse,
  ValidationResult,
  CreateProfileRequest,
  VisualDescriptionRequest,
  SceneAnalysisRequest,
  PreviewRequest
} from '../types/cinematic';

const API_BASE_URL = '/api/v1/cinematic';

class CinematicApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: any
  ) {
    super(message);
    this.name = 'CinematicApiError';
  }
}

const handleApiResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new CinematicApiError(
      errorData.detail || errorData.message || 'API request failed',
      response.status,
      errorData
    );
  }
  return response.json();
};

const makeRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  return handleApiResponse<T>(response);
};

export class CinematicApiService {
  // Profile Management
  static async getProfiles(userId: string = 'default'): Promise<CinematicProfile[]> {
    return makeRequest<CinematicProfile[]>(`/settings/profiles?user_id=${encodeURIComponent(userId)}`);
  }

  static async getProfile(profileId: string, userId: string = 'default'): Promise<CinematicSettings> {
    const response = await makeRequest<{ settings: CinematicSettings }>(`/settings/profiles/${profileId}?user_id=${encodeURIComponent(userId)}`);
    return response.settings;
  }

  static async createProfile(request: CreateProfileRequest): Promise<{ profile_id: string; status: string }> {
    return makeRequest<{ profile_id: string; status: string }>('/settings/profiles', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  static async updateProfile(profileId: string, request: CreateProfileRequest): Promise<{ profile_id: string; status: string }> {
    return makeRequest<{ profile_id: string; status: string }>(`/settings/profiles/${profileId}`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  }

  static async deleteProfile(profileId: string, userId: string = 'default'): Promise<{ profile_id: string; status: string }> {
    return makeRequest<{ profile_id: string; status: string }>(`/settings/profiles/${profileId}?user_id=${encodeURIComponent(userId)}`, {
      method: 'DELETE',
    });
  }

  // Settings Management
  static async getDefaultSettings(userId: string = 'default'): Promise<CinematicSettings> {
    const response = await makeRequest<{ settings: CinematicSettings }>(`/settings/default?user_id=${encodeURIComponent(userId)}`);
    return response.settings;
  }

  static async validateSettings(settings: CinematicSettings): Promise<ValidationResult> {
    return makeRequest<ValidationResult>('/settings/validate', {
      method: 'POST',
      body: JSON.stringify({ settings }),
    });
  }

  // Visual Description
  static async generateVisualDescription(request: VisualDescriptionRequest): Promise<VisualDescription> {
    return makeRequest<VisualDescription>('/visual-description', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  static async getVisualDescription(sceneId: string): Promise<VisualDescription> {
    return makeRequest<VisualDescription>(`/visual-description/${sceneId}`);
  }

  // Scene Analysis
  static async analyzeScene(request: SceneAnalysisRequest): Promise<{
    scene_analysis: SceneAnalysis;
    cinematic_recommendations: CinematicSettings;
    confidence: number;
  }> {
    return makeRequest<{
      scene_analysis: SceneAnalysis;
      cinematic_recommendations: CinematicSettings;
      confidence: number;
    }>('/scene-analysis', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Preview Generation
  static async generatePreview(request: PreviewRequest): Promise<PreviewResponse> {
    return makeRequest<PreviewResponse>('/preview', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Import/Export
  static async exportProfile(profileId: string, userId: string = 'default'): Promise<{ exported_data: string }> {
    return makeRequest<{ exported_data: string }>(`/settings/export/${profileId}?user_id=${encodeURIComponent(userId)}`, {
      method: 'POST',
    });
  }

  static async importProfile(profileData: string, userId: string = 'default'): Promise<{ profile_id: string; status: string }> {
    return makeRequest<{ profile_id: string; status: string }>('/settings/import', {
      method: 'POST',
      body: JSON.stringify({ profile_data: profileData, user_id: userId }),
    });
  }
}

// Utility functions for API service
export const withRetry = async <T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: Error;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      lastError = error as Error;
      
      if (attempt === maxRetries) {
        throw lastError;
      }

      // Don't retry on client errors (4xx)
      if (error instanceof CinematicApiError && error.status >= 400 && error.status < 500) {
        throw error;
      }

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay * attempt));
    }
  }

  throw lastError!;
};

export const withTimeout = async <T>(
  apiCall: () => Promise<T>,
  timeoutMs: number = 30000
): Promise<T> => {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error('API request timeout')), timeoutMs);
  });

  return Promise.race([apiCall(), timeoutPromise]);
};

// Batch operations
export const batchApiCalls = async <T>(
  apiCalls: (() => Promise<T>)[],
  concurrency: number = 3
): Promise<T[]> => {
  const results: T[] = [];
  
  for (let i = 0; i < apiCalls.length; i += concurrency) {
    const batch = apiCalls.slice(i, i + concurrency);
    const batchResults = await Promise.all(batch.map(call => call()));
    results.push(...batchResults);
  }
  
  return results;
};

// Error handling utilities
export const isApiError = (error: any): error is CinematicApiError => {
  return error instanceof CinematicApiError;
};

export const getErrorMessage = (error: any): string => {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
};

export const isRetryableError = (error: any): boolean => {
  if (isApiError(error)) {
    // Retry on server errors (5xx) but not client errors (4xx)
    return error.status >= 500;
  }
  return true; // Retry on network errors
};

export { CinematicApiError };