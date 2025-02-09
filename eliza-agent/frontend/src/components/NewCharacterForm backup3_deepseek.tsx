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
  // ... keep all existing state and handler functions exactly the same ...
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
    <form onSubmit={handleSubmit} className="space-y-8 max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md">
      {/* Basic Information */}
      <div className="space-y-6 p-6 bg-gray-50 rounded-lg">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Character Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter character name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Model Provider</label>
            <input
              type="text"
              value={formData.modelProvider}
              onChange={e => setFormData(prev => ({ ...prev, modelProvider: e.target.value }))}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., OpenAI"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Voice Model</label>
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
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Voice model identifier"
            />
          </div>
        </div>
      </div>

      {/* Arrays with Add/Remove */}
      {['clients', 'plugins', 'bio', 'lore', 'knowledge', 'postExamples', 'topics', 'adjectives'].map(field => (
        <div key={field} className="space-y-3 p-6 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700 capitalize">
              {field.replace(/([A-Z])/g, ' $1').toLowerCase()}
            </label>
            <button
              type="button"
              onClick={() => addArrayItem(field)}
              className="flex items-center text-sm text-green-600 hover:text-green-700"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add New
            </button>
          </div>
          
          {formData[field].map((item: string, index: number) => (
            <div key={index} className="flex gap-3 items-center">
              <input
                type="text"
                value={item}
                onChange={e => handleArrayChange(field, index, e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="button"
                onClick={() => removeArrayItem(field, index)}
                className="p-2 text-red-500 hover:text-red-700 rounded-full hover:bg-red-50"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      ))}

      {/* Message Examples */}
      <div className="space-y-6 p-6 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-800">Message Examples</h3>
          <button
            type="button"
            onClick={addMessageExample}
            className="flex items-center text-sm text-green-600 hover:text-green-700"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add Example
          </button>
        </div>

        {formData.messageExamples.map((example, exampleIndex) => (
          <div key={exampleIndex} className="p-6 bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="flex justify-between items-center mb-4">
              <h4 className="font-medium text-gray-700">Example {exampleIndex + 1}</h4>
              <button
                type="button"
                onClick={() => removeMessageExample(exampleIndex)}
                className="text-sm text-red-500 hover:text-red-700 flex items-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Remove
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-600">User Message</label>
                <input
                  type="text"
                  value={example[0].content.text}
                  onChange={e => handleMessageExampleChange(exampleIndex, 0, 'text', e.target.value)}
                  placeholder="What the user says..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-600">Assistant Response</label>
                <input
                  type="text"
                  value={example[1].user}
                  onChange={e => handleMessageExampleChange(exampleIndex, 1, 'user', e.target.value)}
                  placeholder="Assistant name/identifier"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 mb-2"
                />
                <input
                  type="text"
                  value={example[1].content.text}
                  onChange={e => handleMessageExampleChange(exampleIndex, 1, 'text', e.target.value)}
                  placeholder="Assistant's response text"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 mb-2"
                />
                <input
                  type="text"
                  value={example[1].content.action || ''}
                  onChange={e => handleMessageExampleChange(exampleIndex, 1, 'action', e.target.value)}
                  placeholder="Optional action"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Style Categories */}
      <div className="space-y-6 p-6 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-medium text-gray-800 mb-4">Styling Options</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.keys(formData.style).map(category => (
            <div key={category} className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700 capitalize">{category}</label>
                <button
                  type="button"
                  onClick={() => addStyleItem(category)}
                  className="text-sm text-green-600 hover:text-green-700"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                </button>
              </div>
              
              {formData.style[category].map((item: string, index: number) => (
                <div key={index} className="flex gap-3 items-center">
                  <input
                    type="text"
                    value={item}
                    onChange={e => handleStyleChange(category, index, e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                    className="p-2 text-red-500 hover:text-red-700"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg flex items-center">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      <div className="flex justify-end gap-4 pt-6 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          className="px-6 py-2 text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-6 py-2 text-white bg-blue-600 rounded-md shadow-sm hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Create Character
        </button>
      </div>
    </form>
  );
};

export default NewCharacterForm;