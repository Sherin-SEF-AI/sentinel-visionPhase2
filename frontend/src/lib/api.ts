/**
 * API client for Sentinel Vision backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Camera API
export interface Camera {
  id: number
  camera_id: string
  name: string
  location: string
  stream_url: string
  facility_zone?: string
  is_active: boolean
  operational_status: string
}

export async function getCameras(): Promise<Camera[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/cameras`)
  if (!response.ok) throw new Error('Failed to fetch cameras')
  return response.json()
}

export async function createCamera(camera: Partial<Camera>): Promise<Camera> {
  const response = await fetch(`${API_BASE_URL}/api/v1/cameras`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(camera)
  })
  if (!response.ok) throw new Error('Failed to create camera')
  return response.json()
}

// Search API
export interface SearchResult {
  query_id: string
  query: string
  results: any[]
  result_count: number
  cameras_searched: number
  frames_evaluated: number
  execution_time_ms: number
  suggestions?: string[]
}

export async function searchVideos(query: string): Promise<SearchResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  })
  if (!response.ok) throw new Error('Failed to search videos')
  return response.json()
}

// Threats API
export interface ThreatAlert {
  id: number
  detection_id: string
  threat_type: string
  severity: string
  confidence_score: number
  detected_at: string
  alert_status: string
  alert_message?: string
  camera?: {
    id: number
    name: string
    location: string
  }
}

export async function getThreats(filters?: {
  severity?: string
  status?: string
}): Promise<ThreatAlert[]> {
  const params = new URLSearchParams()
  if (filters?.severity) params.append('severity', filters.severity)
  if (filters?.status) params.append('status', filters.status)

  const response = await fetch(`${API_BASE_URL}/api/v1/threats/alerts?${params}`)
  if (!response.ok) throw new Error('Failed to fetch threats')
  return response.json()
}

export async function acknowledgeAlert(detectionId: string): Promise<ThreatAlert> {
  const response = await fetch(`${API_BASE_URL}/api/v1/threats/alerts/${detectionId}/acknowledge`, {
    method: 'POST'
  })
  if (!response.ok) throw new Error('Failed to acknowledge alert')
  return response.json()
}

// Tracking API
export interface PersonTrack {
  id: number
  track_id: string
  first_seen: string
  last_seen: string
  duration_seconds: number
  appearance_signature: {
    clothing_upper?: string
    clothing_lower?: string
    colors: string[]
  }
  camera_names?: string[]
  trajectory: Array<{
    timestamp: string
    camera_name?: string
    facility_zone?: string
  }>
  status: string
}

export async function getActiveTracks(): Promise<PersonTrack[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tracking/active`)
  if (!response.ok) throw new Error('Failed to fetch active tracks')
  return response.json()
}

// Dashboard API
export interface DashboardStats {
  cameras: {
    total: number
    active: number
    offline: number
  }
  alerts: {
    active: number
    critical: number
    today: number
  }
  tracking: {
    active_tracks: number
    total_today: number
  }
  system: {
    status: string
    uptime: number
  }
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return {
    cameras: { total: 12, active: 10, offline: 2 },
    alerts: { active: 3, critical: 1, today: 15 },
    tracking: { active_tracks: 24, total_today: 156 },
    system: { status: 'operational', uptime: 99.8 }
  }
}

export async function getRecentActivity(): Promise<any[]> {
  return []
}
