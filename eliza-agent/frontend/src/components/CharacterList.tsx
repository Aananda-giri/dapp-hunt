import { Link } from 'react-router-dom'

interface CharacterListProps {
  characters: Array<{ name: string }>
  selectedNames: string[]
  onSelectionChange: (names: string[]) => void
}

const CharacterList = ({ 
  characters, 
  selectedNames, 
  onSelectionChange 
}: CharacterListProps) => {
  const toggleSelection = (name: string) => {
    const newSelection = selectedNames.includes(name)
      ? selectedNames.filter(n => n !== name)
      : [...selectedNames, name]
    onSelectionChange(newSelection)
  }

  return (
    <div style={{ 
      display: 'grid', 
      gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
      gap: '10px',
      margin: '20px 0'
    }}>
      {characters.map(character => (
        <div 
          key={character.name}
          style={{
            border: '1px solid #ddd',
            padding: '10px',
            borderRadius: '5px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <input
            type="checkbox"
            checked={selectedNames.includes(character.name)}
            onChange={() => toggleSelection(character.name)}
            style={{ width: '20px', height: '20px' }}
          />
          <span style={{ flexGrow: 1 }}>{character.name}</span>
          <Link to={`/edit/${character.name}`} style={{ textDecoration: 'none' }}>
            ✏️
          </Link>
        </div>
      ))}
    </div>
  )
}

export default CharacterList