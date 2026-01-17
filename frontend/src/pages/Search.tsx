import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Search as SearchIcon, Loader2 } from 'lucide-react'
import { searchVideos } from '../lib/api'
import { formatDate, formatConfidence, getConfidenceColor } from '../lib/utils'

export default function Search() {
  const [query, setQuery] = useState('')

  const searchMutation = useMutation({
    mutationFn: (searchQuery: string) => searchVideos(searchQuery),
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      searchMutation.mutate(query)
    }
  }

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <div className="card p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Natural Language Search
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                id="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Show me anyone wearing a red jacket near the main entrance this morning"
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
              <button
                type="submit"
                disabled={searchMutation.isPending}
                className="btn-primary px-6 py-2"
              >
                {searchMutation.isPending ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <>
                    <SearchIcon className="h-5 w-5 mr-2" />
                    Search
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="text-sm text-gray-600">
            <p className="font-medium mb-2">Example queries:</p>
            <ul className="space-y-1 list-disc list-inside">
              <li>Person carrying boxes in the loading dock yesterday afternoon</li>
              <li>Who left the building between 5pm and 6pm last Friday?</li>
              <li>Show suspicious activity in the parking lot last night</li>
              <li>Anyone wearing a blue uniform near the server room today</li>
            </ul>
          </div>
        </form>
      </div>

      {/* Results */}
      {searchMutation.data && (
        <div className="card">
          <div className="border-b px-6 py-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                Search Results ({searchMutation.data.result_count})
              </h3>
              <span className="text-sm text-gray-600">
                Searched {searchMutation.data.cameras_searched} cameras in{' '}
                {searchMutation.data.execution_time_ms}ms
              </span>
            </div>
          </div>

          <div className="divide-y">
            {searchMutation.data.results.map((result: any) => (
              <div key={result.frame_id} className="p-6 hover:bg-gray-50">
                <div className="flex gap-4">
                  {/* Thumbnail placeholder */}
                  <div className="h-32 w-48 flex-shrink-0 rounded-lg bg-gray-200" />

                  <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold">{result.camera.name}</h4>
                        <p className="text-sm text-gray-600">{result.camera.location}</p>
                      </div>
                      <span className={`text-sm font-medium ${getConfidenceColor(result.confidence.total)}`}>
                        {formatConfidence(result.confidence.total)} confidence
                      </span>
                    </div>

                    <p className="text-sm text-gray-700">{result.match_explanation}</p>

                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>{formatDate(result.frame.captured_at)}</span>
                      <span>•</span>
                      <span>{result.analysis.person_count} persons detected</span>
                      {result.analysis.activity_category && (
                        <>
                          <span>•</span>
                          <span>{result.analysis.activity_category}</span>
                        </>
                      )}
                    </div>

                    {result.matched_entities.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {result.matched_entities.map((entity: string) => (
                          <span key={entity} className="badge bg-gray-100 text-gray-700">
                            {entity}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {searchMutation.data.suggestions && searchMutation.data.suggestions.length > 0 && (
            <div className="border-t bg-gray-50 px-6 py-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Refine your search:</p>
              <div className="flex flex-wrap gap-2">
                {searchMutation.data.suggestions.map((suggestion: string, index: number) => (
                  <button
                    key={index}
                    onClick={() => setQuery(suggestion)}
                    className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {searchMutation.isError && (
        <div className="card p-6">
          <p className="text-center text-red-600">
            Error performing search. Please try again.
          </p>
        </div>
      )}
    </div>
  )
}
