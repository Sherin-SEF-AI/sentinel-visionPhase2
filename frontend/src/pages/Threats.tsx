import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle } from 'lucide-react'
import { getThreats, acknowledgeAlert } from '../lib/api'
import { formatDate, getSeverityBadge } from '../lib/utils'

export default function Threats() {
  const queryClient = useQueryClient()

  const { data: threats, isLoading } = useQuery({
    queryKey: ['threats'],
    queryFn: getThreats,
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  const acknowledgeMutation = useMutation({
    mutationFn: acknowledgeAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threats'] })
    },
  })

  if (isLoading) {
    return <div className="text-center py-12">Loading threats...</div>
  }

  const pendingThreats = threats?.filter((t: any) => t.alert_status === 'pending') || []
  const acknowledgedThreats = threats?.filter((t: any) => t.alert_status !== 'pending') || []

  return (
    <div className="space-y-6">
      {/* Pending Threats */}
      <div className="card">
        <div className="border-b px-6 py-4 bg-red-50">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <h3 className="text-lg font-semibold text-red-900">
              Active Threats ({pendingThreats.length})
            </h3>
          </div>
        </div>

        <div className="divide-y">
          {pendingThreats.length > 0 ? (
            pendingThreats.map((threat: any) => (
              <div key={threat.detection_id} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="text-lg font-semibold">{threat.threat_type}</h4>
                      <span className={`badge ${getSeverityBadge(threat.severity)}`}>
                        {threat.severity}
                      </span>
                      <span className="text-sm text-gray-600">
                        {(threat.confidence_score * 100).toFixed(0)}% confidence
                      </span>
                    </div>

                    <p className="text-sm text-gray-700 mb-3">{threat.evidence_summary}</p>

                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>{formatDate(threat.detected_at)}</span>
                      {threat.location && (
                        <>
                          <span>•</span>
                          <span>{threat.location}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => acknowledgeMutation.mutate(threat.detection_id)}
                    disabled={acknowledgeMutation.isPending}
                    className="btn-primary px-4 py-2"
                  >
                    Acknowledge
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="p-12 text-center text-gray-500">
              No active threats detected
            </div>
          )}
        </div>
      </div>

      {/* Acknowledged Threats */}
      {acknowledgedThreats.length > 0 && (
        <div className="card">
          <div className="border-b px-6 py-4">
            <h3 className="text-lg font-semibold">
              Acknowledged Threats ({acknowledgedThreats.length})
            </h3>
          </div>

          <div className="divide-y">
            {acknowledgedThreats.map((threat: any) => (
              <div key={threat.detection_id} className="p-6 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h4 className="font-semibold">{threat.threat_type}</h4>
                      <span className={`badge ${getSeverityBadge(threat.severity)}`}>
                        {threat.severity}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{formatDate(threat.detected_at)}</p>
                  </div>
                  <span className="badge badge-success">{threat.alert_status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
