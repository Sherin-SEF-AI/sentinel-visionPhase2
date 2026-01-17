import { useQuery } from '@tanstack/react-query'
import { Users, MapPin, Clock } from 'lucide-react'
import { getActiveTracks } from '../lib/api'
import { formatDate } from '../lib/utils'

export default function Tracking() {
  const { data: tracks, isLoading } = useQuery({
    queryKey: ['tracks'],
    queryFn: getActiveTracks,
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  if (isLoading) {
    return <div className="text-center py-12">Loading active tracks...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-semibold">Active Person Tracks</h3>
            <p className="text-sm text-gray-600 mt-1">
              Real-time tracking of persons across cameras (last 5 minutes)
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold">{tracks?.length || 0}</p>
            <p className="text-sm text-gray-600">Active Now</p>
          </div>
        </div>
      </div>

      {/* Tracks */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {tracks && tracks.length > 0 ? (
          tracks.map((track: any) => (
            <div key={track.track_id} className="card p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-primary-100 p-3">
                    <Users className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold">{track.track_id}</h4>
                    <p className="text-sm text-gray-600">
                      {track.frame_count} frames • {track.duration_seconds}s duration
                    </p>
                  </div>
                </div>
                <span className="badge badge-success">Active</span>
              </div>

              {/* Appearance */}
              <div className="mb-4">
                <h5 className="text-sm font-semibold text-gray-700 mb-2">Appearance</h5>
                <p className="text-sm text-gray-600">{track.clothing_description}</p>
                {track.distinctive_features && track.distinctive_features.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {track.distinctive_features.map((feature: string, index: number) => (
                      <span key={index} className="badge bg-gray-100 text-gray-700 text-xs">
                        {feature}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Timeline */}
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <Clock className="h-4 w-4" />
                  <span>First seen: {formatDate(track.first_seen)}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <Clock className="h-4 w-4" />
                  <span>Last seen: {formatDate(track.last_seen)}</span>
                </div>
              </div>

              {/* Cameras */}
              {track.camera_names && track.camera_names.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <h5 className="text-sm font-semibold text-gray-700 mb-2">
                    Cameras ({track.camera_names.length})
                  </h5>
                  <div className="flex flex-wrap gap-2">
                    {track.camera_names.map((camera: string, index: number) => (
                      <span key={index} className="badge bg-blue-100 text-blue-800 text-xs">
                        <MapPin className="h-3 w-3 mr-1" />
                        {camera}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Confidence */}
              {track.confidence_score && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">Track Confidence</span>
                    <span className="font-medium">{(track.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{ width: `${track.confidence_score * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="col-span-2 card p-12">
            <p className="text-center text-gray-500">
              No active person tracks in the last 5 minutes
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
