import { useState, useEffect } from 'react'
import axios from 'axios'
import NewCharacterForm from './NewCharacterForm'
import CharacterList from './CharacterList'

interface Character {
  name: string
  [key: string]: any
}

const HomePage = () => {
  const [showNewForm, setShowNewForm] = useState(false)
  const [characters, setCharacters] = useState<Character[]>([])
  const [selectedNames, setSelectedNames] = useState<string[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    fetchCharacters()
  }, [])

  const fetchCharacters = async () => {
    try {
      const response = await axios.get('/api/characters')
      setCharacters(response.data)
    } catch (err) {
      setError('Failed to fetch characters')
    }
  }

  const handleRunAgents = async () => {
    if (!selectedNames.length) return
    
    if (!window.confirm(
      'This will stop agents running in background. Continue?'
    )) return

    try {
      const response = await axios.post('/api/characters/run', {
        characters: selectedNames
      })
      alert(`Success! ${response.data.message}`)
    } catch (err) {
      alert('Error running agents')
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Character Manager</h1>
      
      {/* Step 1: New Character */}
      <section style={{ marginBottom: '40px' }}>
        <h2>Create New Character</h2>
        {showNewForm ? (
          <NewCharacterForm 
            onCancel={() => setShowNewForm(false)}
            onSuccess={() => {
              setShowNewForm(false)
              fetchCharacters()
            }}
          />
        ) : (
          <button 
            onClick={() => setShowNewForm(true)}
            style={{ padding: '10px 20px', fontSize: '1.1rem' }}
          >
            ➕ New Character
          </button>
        )}
      </section>

      {/* Step 2: Character List */}
      <section>
        <h2>Step 2: Manage Characters</h2>
        {error && <div style={{ color: 'red' }}>{error}</div>}
        
        <CharacterList 
          characters={characters}
          selectedNames={selectedNames}
          onSelectionChange={setSelectedNames}
        />
        
        <button
          onClick={handleRunAgents}
          disabled={!selectedNames.length}
          style={{
            marginTop: '20px',
            padding: '10px 30px',
            fontSize: '1.1rem',
            backgroundColor: selectedNames.length && '#4CAF50',
            // backgroundColor: selectedNames.length ? '#4CAF50' : '#ccc',
            color: 'white'
          }}
        >
          Run Selected characters
        </button>
      </section>
    </div>
  )
}

export default HomePage

// {{ padding: '10px 20px', fontSize: '1.1rem' }}