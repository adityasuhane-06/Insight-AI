import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import NewSession from './pages/NewSession'
import SessionDetail from './pages/SessionDetail'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="new" element={<NewSession />} />
          <Route path="sessions/:id" element={<SessionDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
