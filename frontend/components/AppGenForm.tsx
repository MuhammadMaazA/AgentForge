"use client";

import { useState } from 'react';

interface AppGenFormProps {
  onSubmit: (formDataJson: string) => void;
}

export function AppGenForm({ onSubmit }: AppGenFormProps) {
  const [appName, setAppName] = useState('');
  const [appType, setAppType] = useState('nextjs');
  const [features, setFeatures] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const formData = {
      appName,
      appType,
      // Split features by newline or comma, and filter out empty strings
      features: features.split(/[\n,]+/).map(f => f.trim()).filter(f => f),
      description,
    };
    onSubmit(JSON.stringify(formData));
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-4xl font-bold mb-8">AgentForge</h1>
      <p className="text-lg mb-8 text-gray-400">Describe the application you want to build, and our AI will generate it for you.</p>
      <form onSubmit={handleSubmit} className="w-full max-w-2xl bg-gray-800 p-8 rounded-lg shadow-lg">
        
        <div className="mb-6">
          <label htmlFor="appName" className="block mb-2 text-lg font-medium text-gray-300">
            Application Name
          </label>
          <input
            id="appName"
            type="text"
            value={appName}
            onChange={(e) => setAppName(e.target.value)}
            className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., My Awesome Project"
            required
          />
        </div>

        <div className="mb-6">
          <label htmlFor="appType" className="block mb-2 text-lg font-medium text-gray-300">
            Application Type
          </label>
          <select
            id="appType"
            value={appType}
            onChange={(e) => setAppType(e.target.value)}
            className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="nextjs">Next.js</option>
            <option value="react">React (Vite)</option>
            <option value="vue">Vue (Vite)</option>
            <option value="streamlit">Streamlit</option>
            <option value="flask">Flask</option>
            <option value="fastapi">FastAPI</option>
          </select>
        </div>

        <div className="mb-6">
          <label htmlFor="features" className="block mb-2 text-lg font-medium text-gray-300">
            Key Features
          </label>
          <textarea
            id="features"
            value={features}
            onChange={(e) => setFeatures(e.target.value)}
            className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={4}
            placeholder="List the main features, one per line or separated by commas.&#10;e.g., User authentication, &#10;Dashboard to display data, &#10;Real-time chat functionality"
            required
          />
        </div>

        <div className="mb-6">
          <label htmlFor="description" className="block mb-2 text-lg font-medium text-gray-300">
            Detailed Description (Optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={5}
            placeholder="Provide any additional details, context, or specific requirements for your application."
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg text-lg transition-transform transform hover:scale-105"
        >
          Generate Application
        </button>
      </form>
    </div>
  );
}
