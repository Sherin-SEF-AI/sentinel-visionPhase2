import { useQuery } from '@tanstack/react-query'
import { Camera as CameraIcon, MapPin } from 'lucide-react'
import { getCameras } from '../lib/api'

export default function Cameras() {
  const { data, isLoading } = useQuery({
    queryKey: ['cameras'],
    queryFn: getCameras,
  })

  if (isLoading) {
    return <div className="text-center py-12">Loading cameras...</div>
  }

  const cameras = data?.cameras || []
  const activeCameras = cameras.filter((c: any) => c.is_active)
  const inactiveCameras = cameras.filter((c: any) => !c.is_active)

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Cameras</p>
              <p className="text-3xl font-bold">{cameras.length}</p>
            </div>
            <CameraIcon className="h-10 w-10 text-gray-400" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active</p>
              <p className="text-3xl font-bold text-green-600">{activeCameras.length}</p>
            </div>
            <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Inactive</p>
              <p className="text-3xl font-bold text-gray-400">{inactiveCameras.length}</p>
            </div>
            <div className="h-3 w-3 rounded-full bg-gray-300" />
          </div>
        </div>
      </div>

      {/* Active Cameras */}
      <div className="card">
        <div className="border-b px-6 py-4">
          <h3 className="text-lg font-semibold">Active Cameras</h3>
        </div>

        <div className="grid grid-cols-1 gap-4 p-6 lg:grid-cols-2">
          {activeCameras.map((camera: any) => (
            <div key={camera.id} className="rounded-lg border p-4 hover:bg-gray-50">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-green-100 p-2">
                    <CameraIcon className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold">{camera.name}</h4>
                    <p className="text-sm text-gray-600">{camera.camera_id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span className="text-sm text-green-600">Online</span>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <MapPin className="h-4 w-4" />
                  <span>{camera.location}</span>
                </div>

                {camera.facility_zone && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-700">Zone:</span>
                    <span className="badge bg-blue-100 text-blue-800">{camera.facility_zone}</span>
                  </div>
                )}

                <div className="flex items-center gap-4 pt-2">
                  <div>
                    <span className="text-gray-600">FPS: </span>
                    <span className="font-medium">{camera.frame_extraction_fps}</span>
                  </div>
                  {camera.motion_detection_enabled && (
                    <span className="badge bg-purple-100 text-purple-800">
                      Motion Detection
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {activeCameras.length === 0 && (
          <div className="p-12 text-center text-gray-500">
            No active cameras found
          </div>
        )}
      </div>
    </div>
  )
}
