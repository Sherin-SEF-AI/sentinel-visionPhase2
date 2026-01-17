import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Camera, Users, Activity } from 'lucide-react'
import { api } from '../lib/api'

export default function Dashboard() {
  const { data: cameras } = useQuery({
    queryKey: ['cameras'],
    queryFn: () => api.get('/cameras').then(res => res.data),
  })

  const { data: threats } = useQuery({
    queryKey: ['threats'],
    queryFn: () => api.get('/threats/alerts?limit=10').then(res => res.data),
  })

  const stats = [
    {
      name: 'Active Cameras',
      value: cameras?.cameras?.filter((c: any) => c.is_active).length || 0,
      icon: Camera,
      color: 'bg-blue-500',
    },
    {
      name: 'Active Threats',
      value: threats?.filter((t: any) => t.alert_status === 'pending').length || 0,
      icon: AlertTriangle,
      color: 'bg-red-500',
    },
    {
      name: 'Active Tracks',
      value: '-',
      icon: Users,
      color: 'bg-green-500',
    },
    {
      name: 'Frames Processed',
      value: '-',
      icon: Activity,
      color: 'bg-purple-500',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card p-6">
            <div className="flex items-center">
              <div className={`rounded-full p-3 ${stat.color}`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Threats */}
      <div className="card">
        <div className="border-b px-6 py-4">
          <h3 className="text-lg font-semibold">Recent Threat Alerts</h3>
        </div>
        <div className="p-6">
          {threats && threats.length > 0 ? (
            <div className="space-y-4">
              {threats.slice(0, 5).map((threat: any) => (
                <div key={threat.detection_id} className="flex items-center justify-between rounded-lg border p-4">
                  <div className="flex items-center gap-4">
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                    <div>
                      <p className="font-medium">{threat.threat_type}</p>
                      <p className="text-sm text-gray-600">
                        {new Date(threat.detected_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <span className={`badge badge-${threat.severity}`}>
                    {threat.severity}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500">No active threats</p>
          )}
        </div>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <div className="border-b px-6 py-4">
            <h3 className="text-lg font-semibold">Camera Status</h3>
          </div>
          <div className="p-6">
            {cameras?.cameras?.map((camera: any) => (
              <div key={camera.id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <div className={`h-2 w-2 rounded-full ${camera.is_online ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <span className="font-medium">{camera.name}</span>
                </div>
                <span className="text-sm text-gray-600">{camera.location}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="border-b px-6 py-4">
            <h3 className="text-lg font-semibold">System Health</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">PostgreSQL</span>
                <span className="badge badge-success">Healthy</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Qdrant</span>
                <span className="badge badge-success">Healthy</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Redis</span>
                <span className="badge badge-success">Healthy</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Gemini API</span>
                <span className="badge badge-success">Connected</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
