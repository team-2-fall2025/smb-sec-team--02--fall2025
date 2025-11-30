import { Dashboard } from './pages/Dashboard'
import { Health } from './pages/Health'
import { Routes, Route } from 'react-router-dom'
import './App.css'
import { Layout }from './components/Layout'
import { Assets } from './pages/Asset/Assets'
import { IntelEvents } from './pages/IntelEvents'
import { RiskItems } from './pages/RiskItems'
import { AssetViewPage } from './pages/Asset/AssetViewPage'
import { AssetEditPage } from './pages/Asset/AssetEditPage'
import { AssetCreatePage } from './pages/Asset/AssetAddPage'
import { DetectionList } from './pages/Detection/DetectionList'
import { DetectionViewPage } from './pages/Detection/DetectionViewPage'
import { ControlsList } from './pages/Protection/ControlsList'
import { ControlDetailPage } from './pages/Protection/ControlDetailPage'

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
        <Route path="/assets/add" element={<AssetCreatePage />} />
        <Route path="/detections" element={<DetectionList />} />
        <Route path="/detection/:id" element={<DetectionViewPage />} />
        <Route path="/controls" element={<ControlsList />} />
        <Route path="/controls/:control_id" element={<ControlDetailPage />} />
      </Routes>
    </Layout>
  )
}

export default App