/**
 * CinematicProfileManager Component
 * Manages cinematic profiles with CRUD operations, search, and import/export.
 */

import React, { useState, useCallback, useRef } from 'react';
import {
  CinematicProfile,
  CinematicProfileManagerProps,
  CreateProfileRequest
} from '../../types/cinematic';
import { useCinematicProfiles, useProfileForm } from '../../hooks/useCinematicProfiles';

interface ProfileCardProps {
  profile: CinematicProfile;
  isSelected: boolean;
  onSelect: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onExport: () => void;
}

const ProfileCard: React.FC<ProfileCardProps> = ({
  profile,
  isSelected,
  onSelect,
  onEdit,
  onDelete,
  onDuplicate,
  onExport
}) => (
  <div className={`profile-card ${isSelected ? 'selected' : ''} ${profile.is_system ? 'system' : ''}`}>
    <div className="profile-header" onClick={onSelect}>
      <h3 className="profile-name">
        {profile.name}
        {profile.is_default && <span className="default-badge">Default</span>}
        {profile.is_system && <span className="system-badge">System</span>}
      </h3>
      <div className="profile-meta">
        <span className="usage-count">{profile.usage_count} uses</span>
        <span className="last-used">
          Last used: {new Date(profile.last_used).toLocaleDateString()}
        </span>
      </div>
    </div>
    
    <div className="profile-description">
      {profile.description || 'No description'}
    </div>
    
    <div className="profile-validation">
      {!profile.validation.valid && (
        <div className="validation-errors">
          {profile.validation.errors.length} error(s)
        </div>
      )}
      {profile.validation.warnings.length > 0 && (
        <div className="validation-warnings">
          {profile.validation.warnings.length} warning(s)
        </div>
      )}
    </div>
    
    <div className="profile-actions">
      <button onClick={onEdit} disabled={profile.is_system} className="edit-btn">
        Edit
      </button>
      <button onClick={onDuplicate} className="duplicate-btn">
        Duplicate
      </button>
      <button onClick={onExport} className="export-btn">
        Export
      </button>
      <button 
        onClick={onDelete} 
        disabled={profile.is_system || profile.is_default}
        className="delete-btn"
      >
        Delete
      </button>
    </div>
  </div>
);

interface ProfileFormProps {
  profile?: CinematicProfile;
  onSave: (request: CreateProfileRequest) => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
}

const ProfileForm: React.FC<ProfileFormProps> = ({
  profile,
  onSave,
  onCancel,
  isLoading
}) => {
  const { formData, errors, updateField, validateForm, resetForm } = useProfileForm(profile);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      await onSave(formData);
    }
  };

  return (
    <div className="profile-form-overlay">
      <div className="profile-form">
        <h3>{profile ? 'Edit Profile' : 'Create New Profile'}</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Profile Name *</label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => updateField('name', e.target.value)}
              disabled={isLoading}
              className={errors.name ? 'error' : ''}
            />
            {errors.name && <span className="error-text">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => updateField('description', e.target.value)}
              disabled={isLoading}
              rows={3}
              className={errors.description ? 'error' : ''}
            />
            {errors.description && <span className="error-text">{errors.description}</span>}
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.set_as_default}
                onChange={(e) => updateField('set_as_default', e.target.checked)}
                disabled={isLoading}
              />
              Set as default profile
            </label>
          </div>

          <div className="form-actions">
            <button type="button" onClick={onCancel} disabled={isLoading}>
              Cancel
            </button>
            <button type="button" onClick={resetForm} disabled={isLoading}>
              Reset
            </button>
            <button type="submit" disabled={isLoading} className="primary">
              {isLoading ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const CinematicProfileManager: React.FC<CinematicProfileManagerProps> = ({
  userId = 'default',
  onProfileSelect,
  onProfileChange,
  selectedProfileId,
  className = ''
}) => {
  const {
    profiles,
    filteredProfiles,
    selectedProfile,
    isLoading,
    error,
    searchQuery,
    sortBy,
    sortOrder,
    selectProfile,
    createProfile,
    updateProfile,
    deleteProfile,
    duplicateProfile,
    exportProfile,
    importProfile,
    setSearchQuery,
    setSortBy,
    setSortOrder,
    getSystemProfiles,
    getUserProfiles
  } = useCinematicProfiles({ userId, autoLoad: true });

  const [showForm, setShowForm] = useState(false);
  const [editingProfile, setEditingProfile] = useState<CinematicProfile | null>(null);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [importData, setImportData] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle profile selection
  const handleProfileSelect = useCallback((profile: CinematicProfile) => {
    selectProfile(profile.id);
    onProfileSelect?.(profile);
  }, [selectProfile, onProfileSelect]);

  // Handle profile creation
  const handleCreateProfile = useCallback(async (request: CreateProfileRequest) => {
    try {
      const profileId = await createProfile(request);
      setShowForm(false);
      setEditingProfile(null);
      
      // Find and notify about the new profile
      const newProfile = profiles.find(p => p.id === profileId);
      if (newProfile) {
        onProfileChange?.(newProfile);
      }
    } catch (err) {
      // Error is handled by the hook
    }
  }, [createProfile, profiles, onProfileChange]);

  // Handle profile update
  const handleUpdateProfile = useCallback(async (request: CreateProfileRequest) => {
    if (!editingProfile) return;
    
    try {
      await updateProfile(editingProfile.id, request);
      setShowForm(false);
      setEditingProfile(null);
      
      // Find and notify about the updated profile
      const updatedProfile = profiles.find(p => p.id === editingProfile.id);
      if (updatedProfile) {
        onProfileChange?.(updatedProfile);
      }
    } catch (err) {
      // Error is handled by the hook
    }
  }, [editingProfile, updateProfile, profiles, onProfileChange]);

  // Handle profile deletion
  const handleDeleteProfile = useCallback(async (profile: CinematicProfile) => {
    if (!confirm(`Are you sure you want to delete "${profile.name}"?`)) return;
    
    try {
      await deleteProfile(profile.id);
    } catch (err) {
      // Error is handled by the hook
    }
  }, [deleteProfile]);

  // Handle profile duplication
  const handleDuplicateProfile = useCallback(async (profile: CinematicProfile) => {
    const newName = prompt('Enter name for duplicated profile:', `${profile.name} (Copy)`);
    if (!newName) return;
    
    try {
      await duplicateProfile(profile.id, newName);
    } catch (err) {
      // Error is handled by the hook
    }
  }, [duplicateProfile]);

  // Handle profile export
  const handleExportProfile = useCallback(async (profile: CinematicProfile) => {
    try {
      const exportedData = await exportProfile(profile.id);
      
      // Download as file
      const blob = new Blob([exportedData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${profile.name.replace(/[^a-z0-9]/gi, '_')}_profile.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      // Error is handled by the hook
    }
  }, [exportProfile]);

  // Handle profile import
  const handleImportProfile = useCallback(async () => {
    if (!importData.trim()) return;
    
    try {
      await importProfile(importData);
      setShowImportDialog(false);
      setImportData('');
    } catch (err) {
      // Error is handled by the hook
    }
  }, [importProfile, importData]);

  // Handle file import
  const handleFileImport = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setImportData(content);
      setShowImportDialog(true);
    };
    reader.readAsText(file);
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  // Render search and filters
  const renderSearchAndFilters = () => (
    <div className="search-and-filters">
      <div className="search-box">
        <input
          type="text"
          placeholder="Search profiles..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
      </div>
      
      <div className="filters">
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          className="sort-select"
        >
          <option value="last_used">Last Used</option>
          <option value="name">Name</option>
          <option value="usage_count">Usage Count</option>
        </select>
        
        <button
          onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
          className="sort-order-btn"
        >
          {sortOrder === 'asc' ? '↑' : '↓'}
        </button>
      </div>
    </div>
  );

  // Render profile sections
  const renderProfileSections = () => {
    const systemProfiles = getSystemProfiles();
    const userProfiles = getUserProfiles();
    
    return (
      <div className="profile-sections">
        {systemProfiles.length > 0 && (
          <div className="profile-section">
            <h3>System Profiles</h3>
            <div className="profile-grid">
              {systemProfiles
                .filter(profile => 
                  !searchQuery || 
                  profile.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  profile.description.toLowerCase().includes(searchQuery.toLowerCase())
                )
                .map(profile => (
                  <ProfileCard
                    key={profile.id}
                    profile={profile}
                    isSelected={profile.id === selectedProfileId}
                    onSelect={() => handleProfileSelect(profile)}
                    onEdit={() => {
                      setEditingProfile(profile);
                      setShowForm(true);
                    }}
                    onDelete={() => handleDeleteProfile(profile)}
                    onDuplicate={() => handleDuplicateProfile(profile)}
                    onExport={() => handleExportProfile(profile)}
                  />
                ))}
            </div>
          </div>
        )}
        
        <div className="profile-section">
          <h3>My Profiles</h3>
          <div className="profile-grid">
            {filteredProfiles
              .filter(profile => !profile.is_system)
              .map(profile => (
                <ProfileCard
                  key={profile.id}
                  profile={profile}
                  isSelected={profile.id === selectedProfileId}
                  onSelect={() => handleProfileSelect(profile)}
                  onEdit={() => {
                    setEditingProfile(profile);
                    setShowForm(true);
                  }}
                  onDelete={() => handleDeleteProfile(profile)}
                  onDuplicate={() => handleDuplicateProfile(profile)}
                  onExport={() => handleExportProfile(profile)}
                />
              ))}
          </div>
          
          {userProfiles.length === 0 && !searchQuery && (
            <div className="empty-state">
              <p>No custom profiles yet. Create your first profile to get started!</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={`cinematic-profile-manager ${className}`}>
      <div className="manager-header">
        <h2>Cinematic Profiles</h2>
        <div className="header-actions">
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileImport}
            style={{ display: 'none' }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="import-btn"
          >
            Import
          </button>
          <button
            onClick={() => {
              setEditingProfile(null);
              setShowForm(true);
            }}
            disabled={isLoading}
            className="create-btn primary"
          >
            Create Profile
          </button>
        </div>
      </div>

      {error && (
        <div className="error-display">
          <strong>Error:</strong> {error}
        </div>
      )}

      {renderSearchAndFilters()}
      {renderProfileSections()}

      {showForm && (
        <ProfileForm
          profile={editingProfile || undefined}
          onSave={editingProfile ? handleUpdateProfile : handleCreateProfile}
          onCancel={() => {
            setShowForm(false);
            setEditingProfile(null);
          }}
          isLoading={isLoading}
        />
      )}

      {showImportDialog && (
        <div className="import-dialog-overlay">
          <div className="import-dialog">
            <h3>Import Profile</h3>
            <textarea
              value={importData}
              onChange={(e) => setImportData(e.target.value)}
              placeholder="Paste profile JSON data here..."
              rows={10}
              className="import-textarea"
            />
            <div className="dialog-actions">
              <button
                onClick={() => {
                  setShowImportDialog(false);
                  setImportData('');
                }}
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleImportProfile}
                disabled={isLoading || !importData.trim()}
                className="primary"
              >
                {isLoading ? 'Importing...' : 'Import'}
              </button>
            </div>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner">Loading...</div>
        </div>
      )}
    </div>
  );
};