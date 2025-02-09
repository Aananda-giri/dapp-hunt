import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

const NewCharacterForm = ({ onCancel, onSuccess }: { 
  onCancel: () => void
  onSuccess: () => void
}) => {
  const [jsonData, setJsonData] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const parsedData = JSON.parse(jsonData)
      await axios.post('/api/characters', parsedData)
      onSuccess()
    } catch (err: any) {
      setError(err.response?.data?.error || 'Invalid JSON format')
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <textarea
        value={jsonData}
        onChange={(e) => setJsonData(e.target.value)}
        placeholder="Paste character JSON here"
        style={{
          height: '300px',
          width: '100%',
          fontFamily: 'monospace',
          padding: '10px'
        }}
      />
      
      {error && <div style={{ color: 'red' }}>{error}</div>}
      
      <div style={{ display: 'flex', gap: '10px' }}>
        <button type="submit" style={{ padding: '10px 20px' }}>
          Create Character
        </button>
        <button 
          type="button" 
          onClick={onCancel}
          style={{ padding: '10px 20px' }}
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default NewCharacterForm