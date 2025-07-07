import { useState } from 'react'

const EXAMPLE_APPS = [
  {
    name: "TaskManager",
    type: "streamlit",
    features: ["Add and delete tasks", "Mark tasks as complete", "Filter by status", "Save to local storage"],
    description: "A clean and simple task management app with persistent storage"
  },
  {
    name: "WeatherDashboard", 
    type: "streamlit",
    features: ["Current weather display", "5-day forecast", "City search", "Temperature charts"],
    description: "Interactive weather dashboard with beautiful visualizations"
  },
  {
    name: "BlogAPI",
    type: "fastapi", 
    features: ["Create/read/update/delete posts", "User authentication", "Comments system", "Search functionality"],
    description: "RESTful API for a blog platform with full CRUD operations"
  },
  {
    name: "InventoryTracker",
    type: "flask",
    features: ["Product management", "Stock tracking", "Low stock alerts", "Export to CSV"],
    description: "Web application for managing inventory with reporting features"
  }
]

interface ExampleCardProps {
  app: typeof EXAMPLE_APPS[0]
  onUse: (app: typeof EXAMPLE_APPS[0]) => void
}

function ExampleCard({ app, onUse }: ExampleCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-semibold text-gray-900">{app.name}</h4>
        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
          {app.type}
        </span>
      </div>
      <p className="text-sm text-gray-600 mb-3">{app.description}</p>
      <div className="mb-3">
        <p className="text-xs font-medium text-gray-700 mb-1">Features:</p>
        <ul className="text-xs text-gray-600 space-y-1">
          {app.features.slice(0, 3).map((feature, idx) => (
            <li key={idx}>• {feature}</li>
          ))}
          {app.features.length > 3 && (
            <li className="text-gray-500">+ {app.features.length - 3} more...</li>
          )}
        </ul>
      </div>
      <button
        onClick={() => onUse(app)}
        className="w-full px-3 py-1.5 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
      >
        Use This Example
      </button>
    </div>
  )
}

export default function Examples() {
  const [selectedApp, setSelectedApp] = useState<typeof EXAMPLE_APPS[0] | null>(null)

  return (
    <div className="bg-gray-50 rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          💡 Example Applications
        </h3>
        <span className="text-sm text-gray-500">
          Click to use as template
        </span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {EXAMPLE_APPS.map((app, index) => (
          <ExampleCard 
            key={index} 
            app={app} 
            onUse={setSelectedApp}
          />
        ))}
      </div>

      {selectedApp && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <div className="flex justify-between items-start">
            <div>
              <h4 className="font-semibold text-blue-900 mb-1">
                Template Selected: {selectedApp.name}
              </h4>
              <p className="text-sm text-blue-700">
                The form has been populated with this example. You can modify it as needed.
              </p>
            </div>
            <button
              onClick={() => setSelectedApp(null)}
              className="text-blue-600 hover:text-blue-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
