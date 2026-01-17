import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Search from './pages/Search'
import Threats from './pages/Threats'
import Cameras from './pages/Cameras'
import Tracking from './pages/Tracking'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="search" element={<Search />} />
          <Route path="threats" element={<Threats />} />
          <Route path="cameras" element={<Cameras />} />
          <Route path="tracking" element={<Tracking />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
