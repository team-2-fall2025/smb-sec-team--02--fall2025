import { Dashboard } from './pages/Dashboard'
import { Health } from './pages/Health'
import { Routes, Route } from 'react-router-dom'
import './App.css'
import { Layout }from './components/Layout'
import { Assets } from './pages/Assets'
import { IntelEvents } from './pages/IntelEvents'
import { RiskItems } from './pages/RiskItems'
import { AssetViewPage } from './pages/AssetViewPage'
import { AssetEditPage } from './pages/AssetEditPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/assets" element={<Assets />} />
        <Route path="/intel" element={<IntelEvents />} />
        <Route path="/risk" element={<RiskItems />} />
        <Route path="/health" element={<Health />} />
        <Route path="/assets/:id" element={<AssetViewPage />} />
        <Route path="/assets/edit/:id" element={<AssetEditPage />} />
      </Routes>
    </Layout>
  )
}

export default App