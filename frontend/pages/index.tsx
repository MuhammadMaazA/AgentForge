import { useState } from 'react'

interface AppGenerationRequest {
  app_name: string
  features: string[]
  app_type: string
  description?: string
}

interface CodeGenerationResponse {
  success: boolean
  generated_code?: string
  error?: string
  app_name: string
  features: string[]
  ai_provider: string
}

export default function Home() {
  const [formData, setFormData] = useState<AppGenerationRequest>({
    app_name: '',
    features: [''],
    app_type: 'streamlit',
    description: ''
  })
  const [response, setResponse] = useState<CodeGenerationResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'form' | 'code'>('form')

  const addFeature = () => {
    setFormData(prev => ({
      ...prev,
      features: [...prev.features, '']
    }))
  }

  const removeFeature = (index: number) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features.filter((_, i) => i !== index)
    }))
  }

  const updateFeature = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features.map((feature, i) => i === index ? value : feature)
    }))
  }

  const generateApp = async () => {
    if (!formData.app_name.trim()) {
      alert('Please enter an app name')
      return
    }

    const validFeatures = formData.features.filter(f => f.trim())
    if (validFeatures.length === 0) {
      alert('Please add at least one feature')
      return
    }

    setIsLoading(true)
    setActiveTab('code')
    
    try {
      const res = await fetch('http://127.0.0.1:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          features: validFeatures
        }),
      })
      
      const data: CodeGenerationResponse = await res.json()
      setResponse(data)
      
    } catch (error) {
      setResponse({
        success: false,
        error: 'Failed to connect to backend. Make sure the API server is running.',
        app_name: formData.app_name,
        features: formData.features,
        ai_provider: 'unknown'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const copyToClipboard = () => {
    if (response?.generated_code) {
      navigator.clipboard.writeText(response.generated_code)
      alert('Code copied to clipboard!')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                🚀 AgentForge
              </h1>
              <span className="ml-2 text-sm text-gray-500">
                AI-Powered App Generator
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                {response?.ai_provider && `Using ${response.ai_provider}`}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('form')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'form'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📝 App Configuration
            </button>
            <button
              onClick={() => setActiveTab('code')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'code'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              💻 Generated Code
            </button>
          </nav>
        </div>

        {/* Form Tab */}
        {activeTab === 'form' && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left Column - Form */}
              <div className="space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    Create Your Application
                  </h2>
                  
                  {/* App Name */}
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      App Name
                    </label>
                    <input
                      type="text"
                      value={formData.app_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, app_name: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., TaskManager, WeatherApp, BlogSystem"
                    />
                  </div>

                  {/* App Type */}
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Application Type
                    </label>
                    <select
                      value={formData.app_type}
                      onChange={(e) => setFormData(prev => ({ ...prev, app_type: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="streamlit">Streamlit (Interactive Web App)</option>
                      <option value="fastapi">FastAPI (REST API)</option>
                      <option value="flask">Flask (Web Application)</option>
                    </select>
                  </div>

                  {/* Features */}
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Features
                    </label>
                    {formData.features.map((feature, index) => (
                      <div key={index} className="flex mb-2">
                        <input
                          type="text"
                          value={feature}
                          onChange={(e) => updateFeature(index, e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="e.g., User authentication, Data visualization"
                        />
                        {formData.features.length > 1 && (
                          <button
                            onClick={() => removeFeature(index)}
                            className="ml-2 px-3 py-2 text-red-600 hover:text-red-800"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      onClick={addFeature}
                      className="mt-2 px-4 py-2 text-sm text-blue-600 hover:text-blue-800"
                    >
                      + Add Feature
                    </button>
                  </div>

                  {/* Description */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Additional Requirements (Optional)
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Any specific requirements, styling preferences, or additional context..."
                    />
                  </div>

                  {/* Generate Button */}
                  <button
                    onClick={generateApp}
                    disabled={isLoading}
                    className={`w-full py-3 px-4 rounded-md font-medium transition-colors ${
                      isLoading
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }`}
                  >
                    {isLoading ? '🔄 Generating...' : '🚀 Generate Application'}
                  </button>
                </div>
              </div>

              {/* Right Column - Preview */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Preview
                </h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">App Name:</span>
                    <span className="ml-2 text-gray-600">
                      {formData.app_name || 'Not specified'}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Type:</span>
                    <span className="ml-2 text-gray-600 capitalize">
                      {formData.app_type}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Features:</span>
                    <ul className="ml-2 mt-1 space-y-1">
                      {formData.features.filter(f => f.trim()).map((feature, index) => (
                        <li key={index} className="text-gray-600">
                          • {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                  {formData.description && (
                    <div>
                      <span className="font-medium text-gray-700">Description:</span>
                      <p className="ml-2 mt-1 text-gray-600">
                        {formData.description}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Code Tab */}
        {activeTab === 'code' && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Generating your application...</p>
              </div>
            ) : response ? (
              <div>
                {response.success ? (
                  <div>
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">
                        ✅ Generated: {response.app_name}
                      </h3>
                      <div className="flex space-x-2">
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                          {response.ai_provider}
                        </span>
                        <button
                          onClick={copyToClipboard}
                          className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                        >
                          📋 Copy Code
                        </button>
                      </div>
                    </div>
                    <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                      {response.generated_code}
                    </pre>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="text-red-500 text-xl mb-4">❌</div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Generation Failed
                    </h3>
                    <p className="text-gray-600 mb-4">{response.error}</p>
                    <button
                      onClick={() => setActiveTab('form')}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Try Again
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-gray-400 text-6xl mb-4">💻</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Ready to Generate
                </h3>
                <p className="text-gray-600 mb-4">
                  Configure your app and click generate to see the magic happen!
                </p>
                <button
                  onClick={() => setActiveTab('form')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Start Building
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
