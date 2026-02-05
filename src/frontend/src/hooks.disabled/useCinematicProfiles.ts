/**
 * React hook for managing cinematic profiles.
 * Provides profile CRUD operations, search, and sorting.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  CinematicProfile,
  CinematicSettings,
  CreateProfileRequest,
  ProfileManagerState
} from '../types/cinematic';
import { CinematicApiService, withRetry, getErrorMessage } from '../services/cinematicApi';

interface UseCinematicProfilesOptions {
  userId?: string;
  autoLoad?: boolean;
  sortBy?: 'name' | 'last_used' | 'usage_count';
  sortOrder?: 'asc' | 'desc';
}

interface UseCinematicProfilesReturn {
  profiles: CinematicProfile[];
  filteredProfiles: CinematicProfile[];
  selectedProfile: CinematicProfile | null;
  isLoading: boolean;
  error: string | null;
  
  // State management
  searchQuery: string;
  sortBy: 'name' | 'last_used' | 'usage_count';
  sortOrder: 'asc' | 'desc';
  
  // Actions
  loadProfiles: () => Promise<void>;
  selectProfile: (profileId: string | null) => void;
  createProfile: (request: CreateProfileRequest) => Promise<string>;
  updateProfile: (profileId: string, request: CreateProfileRequest) => Promise<void>;
  deleteProfile: (profileId: string) => Promise<void>;
  duplicateProfile: (profileId: string, newName?: string) => Promise<string>;
  
  // Search and sorting
  setSearchQuery: (query: string) => void;
  setSortBy: (sortBy: 'name' | 'last_used' | 'usage_count') => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  
  // Import/Export
  exportProfile: (profileId: string) => Promise<string>;
  importProfile: (profileData: string) => Promise<string>;
  
  // Utility functions
  getDefaultProfile: () => CinematicProfile | null;
  getSystemProfiles: () => CinematicProfile[];
  getUserProfiles: () => CinematicProfile[];
}

export const useCinematicProfiles = (
  options: UseCinematicProfilesOptions = {}
): UseCinematicProfilesReturn => {
  const {
    userId = 'default',
    autoLoad = true,
    sortBy: initialSortBy = 'last_used',
    sortOrder: initialSortOrder = 'desc'
  } = options;

  // State
  const [profiles, setProfiles] = useState<CinematicProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'last_used' | 'usage_count'>(initialSortBy);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>(initialSortOrder);

  // Computed values
  const selectedProfile = useMemo(() => {
    return profiles.find(p => p.id === selectedProfileId) || null;
  }, [profiles, selectedProfileId]);

  const filteredProfiles = useMemo(() => {
    let filtered = profiles;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(profile =>
        profile.name.toLowerCase().includes(query) ||
        profile.description.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: string | number;
      let bValue: string | number;

      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'last_used':
          aValue = new Date(a.last_used).getTime();
          bValue = new Date(b.last_used).getTime();
          break;
        case 'usage_count':
          aValue = a.usage_count;
          bValue = b.usage_count;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [profiles, searchQuery, sortBy, sortOrder]);

  // Actions
  const loadProfiles = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const loadedProfiles = await withRetry(() => 
        CinematicApiService.getProfiles(userId)
      );
      setProfiles(loadedProfiles);
      
      // Auto-select default profile if none selected
      if (!selectedProfileId) {
        const defaultProfile = loadedProfiles.find(p => p.is_default);
        if (defaultProfile) {
          setSelectedProfileId(defaultProfile.id);
        }
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, [userId, selectedProfileId]);

  const selectProfile = useCallback((profileId: string | null) => {
    setSelectedProfileId(profileId);
  }, []);

  const createProfile = useCallback(async (request: CreateProfileRequest): Promise<string> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await withRetry(() => 
        CinematicApiService.createProfile({ ...request, user_id: userId })
      );
      
      // Reload profiles to get the new one
      await loadProfiles();
      
      // Select the new profile
      setSelectedProfileId(response.profile_id);
      
      return response.profile_id;
    } catch (err) {
      setError(getErrorMessage(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [userId, loadProfiles]);

  const updateProfile = useCallback(async (profileId: string, request: CreateProfileRequest): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await withRetry(() => 
        CinematicApiService.updateProfile(profileId, { ...request, user_id: userId })
      );
      
      // Reload profiles to get the updated data
      await loadProfiles();
    } catch (err) {
      setError(getErrorMessage(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [userId, loadProfiles]);

  const deleteProfile = useCallback(async (profileId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await withRetry(() => 
        CinematicApiService.deleteProfile(profileId, userId)
      );
      
      // Remove from local state
      setProfiles(current => current.filter(p => p.id !== profileId));
      
      // Deselect if it was selected
      if (selectedProfileId === profileId) {
        setSelectedProfileId(null);
      }
    } catch (err) {
      setError(getErrorMessage(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [userId, selectedProfileId]);

  const duplicateProfile = useCallback(async (profileId: string, newName?: string): Promise<string> => {
    const originalProfile = profiles.find(p => p.id === profileId);
    if (!originalProfile) {
      throw new Error('Profile not found');
    }

    const duplicateName = newName || `${originalProfile.name} (Copy)`;
    
    const request: CreateProfileRequest = {
      name: duplicateName,
      description: originalProfile.description,
      settings: originalProfile.settings,
      user_id: userId,
      set_as_default: false
    };

    return createProfile(request);
  }, [profiles, userId, createProfile]);

  // Import/Export
  const exportProfile = useCallback(async (profileId: string): Promise<string> => {
    setError(null);

    try {
      const response = await withRetry(() => 
        CinematicApiService.exportProfile(profileId, userId)
      );
      return response.exported_data;
    } catch (err) {
      setError(getErrorMessage(err));
      throw err;
    }
  }, [userId]);

  const importProfile = useCallback(async (profileData: string): Promise<string> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await withRetry(() => 
        CinematicApiService.importProfile(profileData, userId)
      );
      
      // Reload profiles to include the imported one
      await loadProfiles();
      
      return response.profile_id;
    } catch (err) {
      setError(getErrorMessage(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [userId, loadProfiles]);

  // Utility functions
  const getDefaultProfile = useCallback((): CinematicProfile | null => {
    return profiles.find(p => p.is_default && p.user_id === userId) || null;
  }, [profiles, userId]);

  const getSystemProfiles = useCallback((): CinematicProfile[] => {
    return profiles.filter(p => p.is_system);
  }, [profiles]);

  const getUserProfiles = useCallback((): CinematicProfile[] => {
    return profiles.filter(p => !p.is_system && p.user_id === userId);
  }, [profiles, userId]);

  // Load profiles on mount
  useEffect(() => {
    if (autoLoad) {
      loadProfiles();
    }
  }, [autoLoad, loadProfiles]);

  return {
    profiles,
    filteredProfiles,
    selectedProfile,
    isLoading,
    error,
    
    // State
    searchQuery,
    sortBy,
    sortOrder,
    
    // Actions
    loadProfiles,
    selectProfile,
    createProfile,
    updateProfile,
    deleteProfile,
    duplicateProfile,
    
    // Search and sorting
    setSearchQuery,
    setSortBy,
    setSortOrder,
    
    // Import/Export
    exportProfile,
    importProfile,
    
    // Utilities
    getDefaultProfile,
    getSystemProfiles,
    getUserProfiles
  };
};

// Hook for profile form management
export const useProfileForm = (initialProfile?: CinematicProfile) => {
  const [formData, setFormData] = useState<CreateProfileRequest>({
    name: initialProfile?.name || '',
    description: initialProfile?.description || '',
    settings: initialProfile?.settings || {} as CinematicSettings,
    user_id: initialProfile?.user_id || 'default',
    set_as_default: initialProfile?.is_default || false
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const updateField = useCallback(<K extends keyof CreateProfileRequest>(
    field: K,
    value: CreateProfileRequest[K]
  ) => {
    setFormData(current => ({ ...current, [field]: value }));
    
    // Clear error for this field
    if (errors[field]) {
      setErrors(current => {
        const { [field]: _, ...rest } = current;
        return rest;
      });
    }
  }, [errors]);

  const validateForm = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Profile name is required';
    } else if (formData.name.length > 100) {
      newErrors.name = 'Profile name must be 100 characters or less';
    }

    if (formData.description.length > 500) {
      newErrors.description = 'Description must be 500 characters or less';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  const resetForm = useCallback(() => {
    setFormData({
      name: initialProfile?.name || '',
      description: initialProfile?.description || '',
      settings: initialProfile?.settings || {} as CinematicSettings,
      user_id: initialProfile?.user_id || 'default',
      set_as_default: initialProfile?.is_default || false
    });
    setErrors({});
  }, [initialProfile]);

  return {
    formData,
    errors,
    updateField,
    validateForm,
    resetForm,
    isValid: Object.keys(errors).length === 0
  };
};