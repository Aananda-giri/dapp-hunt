import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const NewCharacterForm = ({ 
  onCancel, 
  onSuccess 
}: { 
  onCancel: () => void;
  onSuccess: () => void;
}) => {
  const [formData, setFormData] = useState({
    name: '',
    clients: [''],
    modelProvider: '',
    settings: {
      voice: {
        model: ''
      }
    },
    plugins: [''],
    bio: [''],
    lore: [''],
    knowledge: [''],
    messageExamples: [
      [
        {
          user: '{{user1}}',
          content: { 
            text: '',
            action: '' 
          }
        },
        {
          user: '',
          content: { 
            text: '',
            action: '' 
          }
        }
      ]
    ],
    postExamples: [''],
    topics: [''],
    style: {
      all: [''],
      chat: [''],
      post: ['']
    },
    adjectives: ['']
  });

  const [error, setError] = useState('');

  const handleArrayChange = (field: string, index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].map((item: string, i: number) => 
        i === index ? value : item
      )
    }));
  };

  const addArrayItem = (field: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }));
  };

  const removeArrayItem = (field: string, index: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_: string, i: number) => i !== index)
    }));
  };

  const handleStyleChange = (category: string, index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      style: {
        ...prev.style,
        [category]: prev.style[category].map((item: string, i: number) =>
          i === index ? value : item
        )
      }
    }));
  };

  const addStyleItem = (category: string) => {
    setFormData(prev => ({
      ...prev,
      style: {
        ...prev.style,
        [category]: [...prev.style[category], '']
      }
    }));
  };

  // New functions for handling message examples
  const handleMessageExampleChange = (
    exampleIndex: number,
    messageIndex: number,
    field: 'user' | 'text' | 'action',
    value: string
  ) => {
    setFormData(prev => ({
      ...prev,
      messageExamples: prev.messageExamples.map((example, i) => {
        if (i !== exampleIndex) return example;
        return example.map((message, j) => {
          if (j !== messageIndex) return message;
          if (field === 'user') {
            return { ...message, user: value };
          } else {
            return {
              ...message,
              content: {
                ...message.content,
                [field]: value
              }
            };
          }
        });
      })
    }));
  };

  const addMessageExample = () => {
    setFormData(prev => ({
      ...prev,
      messageExamples: [
        ...prev.messageExamples,
        [
          {
            user: '{{user1}}',
            content: { text: '', action: '' }
          },
          {
            user: '',
            content: { text: '', action: '' }
          }
        ]
      ]
    }));
  };

  const removeMessageExample = (index: number) => {
    setFormData(prev => ({
      ...prev,
      messageExamples: prev.messageExamples.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Clean up the data before sending
      const cleanData = {
        ...formData,
        messageExamples: formData.messageExamples.map(example =>
          example.map(message => ({
            ...message,
            content: message.content.action
              ? { ...message.content }
              : { text: message.content.text }
          }))
        )
      };
      await axios.post('/api/characters', cleanData);
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error creating character');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full p-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Model Provider</label>
          <input
            type="text"
            value={formData.modelProvider}
            onChange={e => setFormData(prev => ({ ...prev, modelProvider: e.target.value }))}
            className="w-full p-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Voice Model</label>
          <input
            type="text"
            value={formData.settings.voice.model}
            onChange={e => setFormData(prev => ({
              ...prev,
              settings: {
                ...prev.settings,
                voice: { ...prev.settings.voice, model: e.target.value }
              }
            }))}
            className="w-full p-2 border rounded"
          />
        </div>
      </div>

      {/* Arrays with Add/Remove */}
      {['clients', 'plugins', 'bio', 'lore', 'knowledge', 'postExamples', 'topics', 'adjectives'].map(field => (
        <div key={field} className="space-y-2">
          <label className="block text-sm font-medium capitalize">{field}</label>
          {formData[field].map((item: string, index: number) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={item}
                onChange={e => handleArrayChange(field, index, e.target.value)}
                className="flex-1 p-2 border rounded"
              />
              <button
                type="button"
                onClick={() => removeArrayItem(field, index)}
                className="px-3 py-1 bg-red-100 text-red-600 rounded hover:bg-red-200"
              >
                -
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() => addArrayItem(field)}
            className="px-3 py-1 bg-green-100 text-green-600 rounded hover:bg-green-200"
          >
            + Add {field.replace(/([A-Z])/g, ' $1').toLowerCase()}
          </button>
        </div>
      ))}

      {/* Message Examples */}
      <div className="space-y-4">
        <label className="block text-sm font-medium">Message Examples</label>
        {formData.messageExamples.map((example, exampleIndex) => (
          <div key={exampleIndex} className="p-4 border rounded space-y-4 bg-gray-50">
            <div className="flex justify-between items-center">
              <h4 className="font-medium">Example {exampleIndex + 1}</h4>
              <button
                type="button"
                onClick={() => removeMessageExample(exampleIndex)}
                className="px-3 py-1 bg-red-100 text-red-600 rounded hover:bg-red-200"
              >
                Remove Example
              </button>
            </div>
            
            {/* User Message */}
            <div className="space-y-2 p-3 bg-white rounded">
              <h5 className="text-sm font-medium">User Message</h5>
              <input
                type="text"
                value={example[0].content.text}
                onChange={e => handleMessageExampleChange(exampleIndex, 0, 'text', e.target.value)}
                placeholder="User message"
                className="w-full p-2 border rounded"
              />
            </div>

            {/* Assistant Message */}
            <div className="space-y-2 p-3 bg-white rounded">
              <h5 className="text-sm font-medium">Assistant Message</h5>
              <input
                type="text"
                value={example[1].user}
                onChange={e => handleMessageExampleChange(exampleIndex, 1, 'user', e.target.value)}
                placeholder="Assistant name"
                className="w-full p-2 border rounded mb-2"
              />
              <input
                type="text"
                value={example[1].content.text}
                onChange={e => handleMessageExampleChange(exampleIndex, 1, 'text', e.target.value)}
                placeholder="Assistant response"
                className="w-full p-2 border rounded mb-2"
              />
              <input
                type="text"
                value={example[1].content.action || ''}
                onChange={e => handleMessageExampleChange(exampleIndex, 1, 'action', e.target.value)}
                placeholder="Action (optional)"
                className="w-full p-2 border rounded"
              />
            </div>
          </div>
        ))}
        <button
          type="button"
          onClick={addMessageExample}
          className="px-3 py-1 bg-green-100 text-green-600 rounded hover:bg-green-200"
        >
          + Add Message Example
        </button>
      </div>

      {/* Style Categories */}
      <div className="space-y-4">
        <h3 className="font-medium">Style</h3>
        {Object.keys(formData.style).map(category => (
          <div key={category} className="space-y-2">
            <label className="block text-sm capitalize">{category}</label>
            {formData.style[category].map((item: string, index: number) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={item}
                  onChange={e => handleStyleChange(category, index, e.target.value)}
                  className="flex-1 p-2 border rounded"
                />
                <button
                  type="button"
                  onClick={() => {
                    setFormData(prev => ({
                      ...prev,
                      style: {
                        ...prev.style,
                        [category]: prev.style[category].filter((_: string, i: number) => i !== index)
                      }
                    }));
                  }}
                  className="px-3 py-1 bg-red-100 text-red-600 rounded hover:bg-red-200"
                >
                  -
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={() => addStyleItem(category)}
              className="px-3 py-1 bg-green-100 text-green-600 rounded hover:bg-green-200"
            >
              + Add {category} style
            </button>
          </div>
        ))}
      </div>

      {error && <div className="text-red-600">{error}</div>}

      <div className="flex gap-4">
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Create Character
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

export default NewCharacterForm;