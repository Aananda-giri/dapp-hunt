import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './components/HomePage'
import EditCharacterForm from './components/EditCharacterForm'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/edit/:name" element={<EditCharacterForm />} />
      </Routes>
    </Router>
  )
}

export default App