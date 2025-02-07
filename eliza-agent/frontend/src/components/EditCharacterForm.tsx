import { useState, useEffect } from 'react'
import axios from 'axios'
import { useParams, useNavigate } from 'react-router-dom'

const EditCharacterForm = () => {
  const { name } = useParams()
  const navigate = useNavigate()
  const [jsonData, setJsonData] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchCharacter = async () => {
      try {
        const response = await axios.get(`/api/characters?name=${name}`)
        setJsonData(JSON.stringify(response.data, null, 2))
      } catch (err) {
        setError('Failed to load character')
      }
    }
    fetchCharacter()
  }, [name])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const parsedData = JSON.parse(jsonData)
      await axios.post('/api/characters/update', parsedData)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.error || 'Invalid JSON format')
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Edit Character: {name}</h2>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <textarea
          value={jsonData}
          onChange={(e) => setJsonData(e.target.value)}
          style={{
            height: '500px',
            width: '100%',
            fontFamily: 'monospace',
            padding: '10px'
          }}
        />
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" style={{ padding: '10px 20px' }}>
            Update Character
          </button>
          <button 
            type="button" 
            onClick={() => navigate('/')}
            style={{ padding: '10px 20px' }}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}

export default EditCharacterForm