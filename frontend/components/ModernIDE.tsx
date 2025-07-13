"use client";

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { ChevronRight, Play, Settings, FileText, Code } from 'lucide-react';

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

// Import existing IDE component
const IDEWithNoSSR = dynamic(() => import('./IDE'), { ssr: false });

interface ModernIDEProps {}

export function ModernIDE({}: ModernIDEProps) {
  const [markdownPrompt, setMarkdownPrompt] = useState(`# Describe your application

## Application Name
My Awesome Project

## Type
Next.js Web Application

## Features
- User authentication and login
- Dashboard with analytics
- Real-time notifications
- Responsive design
- API integration

## Description
Create a modern web application with a clean, professional design. The app should have a landing page, user authentication, and a main dashboard where users can view their data and analytics.

## Additional Requirements
- Use TypeScript
- Include dark/light mode toggle
- Make it mobile-responsive
- Add loading states and error handling`);

  const [jsonPrompt, setJsonPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showIDE, setShowIDE] = useState(false);

  const handleGenerate = () => {
    // Parse the markdown prompt into the format expected by the backend
    const formData = parseMarkdownPrompt(markdownPrompt);
    const jsonPromptString = JSON.stringify(formData);
    
    setJsonPrompt(jsonPromptString);
    setIsGenerating(true);
    setShowIDE(true);
  };

  // Helper function to parse markdown prompt into structured data
  const parseMarkdownPrompt = (markdownPrompt: string) => {
    const lines = markdownPrompt.split('\n');
    let appName = 'My App';
    let appType = 'nextjs';
    let features: string[] = [];
    let description = '';
    
    let currentSection = '';
    let isInFeatures = false;
    let isInDescription = false;
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      if (trimmed.startsWith('## Application Name') || trimmed.startsWith('## Name')) {
        currentSection = 'name';
        continue;
      } else if (trimmed.startsWith('## Type') || trimmed.startsWith('## Application Type')) {
        currentSection = 'type';
        continue;
      } else if (trimmed.startsWith('## Features')) {
        currentSection = 'features';
        isInFeatures = true;
        continue;
      } else if (trimmed.startsWith('## Description') || trimmed.startsWith('## Additional Requirements')) {
        currentSection = 'description';
        isInDescription = true;
        continue;
      } else if (trimmed.startsWith('##')) {
        currentSection = '';
        isInFeatures = false;
        isInDescription = false;
        continue;
      }
      
      if (currentSection === 'name' && trimmed && !trimmed.startsWith('#')) {
        appName = trimmed;
      } else if (currentSection === 'type' && trimmed && !trimmed.startsWith('#')) {
        const typeMap: { [key: string]: string } = {
          'next.js': 'nextjs',
          'nextjs': 'nextjs',
          'react': 'react',
          'vue': 'vue',
          'streamlit': 'streamlit',
          'flask': 'flask',
          'fastapi': 'fastapi'
        };
        const normalizedType = trimmed.toLowerCase().replace(/[^a-z.]/g, '');
        appType = typeMap[normalizedType] || 'nextjs';
      } else if (isInFeatures && trimmed) {
        if (trimmed.startsWith('-') || trimmed.startsWith('•') || trimmed.startsWith('*')) {
          features.push(trimmed.replace(/^[-•*]\s*/, ''));
        } else if (!trimmed.startsWith('#')) {
          features.push(trimmed);
        }
      } else if (isInDescription && trimmed && !trimmed.startsWith('#')) {
        description += (description ? '\n' : '') + trimmed;
      }
    }
    
    return {
      appName,
      appType,
      features,
      description
    };
  };

  const handlePromptChange = (value: string | undefined) => {
    if (value !== undefined) {
      setMarkdownPrompt(value);
    }
  };

  if (showIDE) {
    return <IDEWithNoSSR prompt={jsonPrompt} />;
  }

  return (
    <div className="h-screen bg-[#1e1e1e] text-white flex flex-col">
      {/* Header */}
      <div className="h-14 bg-[#2d2d30] border-b border-[#3e3e42] flex items-center px-6">
        <div className="flex items-center space-x-3">
          <div className="w-6 h-6 bg-[#007acc] rounded flex items-center justify-center">
            <Code className="w-4 h-4 text-white" />
          </div>
          <span className="font-medium text-[#cccccc] text-lg">AgentForge</span>
        </div>
        <div className="ml-auto flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-[#007acc]">
            <div className="w-2 h-2 bg-[#007acc] rounded-full"></div>
            <span>Gemini AI</span>
          </div>
          <button className="p-2 hover:bg-[#3e3e42] rounded transition-colors">
            <Settings className="w-4 h-4 text-[#cccccc]" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Left Panel - Prompt Editor */}
        <div className="w-1/2 border-r border-[#3e3e42] flex flex-col">
          {/* Tab Bar */}
          <div className="h-10 bg-[#2d2d30] border-b border-[#3e3e42] flex items-center px-4">
            <div className="flex items-center space-x-2 text-sm">
              <FileText className="w-4 h-4 text-[#007acc]" />
              <span className="text-[#cccccc]">prompt.md</span>
              <div className="w-2 h-2 bg-[#007acc] rounded-full"></div>
            </div>
          </div>

          {/* Editor Area */}
          <div className="flex-1 relative bg-[#1e1e1e]">
            <MonacoEditor
              height="100%"
              language="markdown"
              theme="vs-dark"
              value={markdownPrompt}
              onChange={handlePromptChange}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
                lineHeight: 1.5,
                padding: { top: 16, bottom: 16 },
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                automaticLayout: true,
                tabSize: 2,
                insertSpaces: true,
                renderWhitespace: 'none',
                folding: false,
                lineNumbers: 'on',
                glyphMargin: false,
                theme: 'vs-dark',
              }}
            />
          </div>

          {/* Action Bar */}
          <div className="h-14 bg-[#2d2d30] border-t border-[#3e3e42] flex items-center justify-between px-4">
            <div className="flex items-center space-x-2 text-sm text-[#858585]">
              <span>Ready to generate</span>
            </div>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="flex items-center space-x-2 bg-[#007acc] hover:bg-[#005a9e] disabled:bg-[#404040] disabled:text-[#858585] text-white px-4 py-2 rounded transition-colors font-medium"
            >
              <Play className="w-4 h-4" />
              <span>{isGenerating ? 'Generating...' : 'Generate App'}</span>
            </button>
          </div>
        </div>

        {/* Right Panel - Preview/Instructions */}
        <div className="w-1/2 flex flex-col bg-[#1e1e1e]">
          {/* Tab Bar */}
          <div className="h-10 bg-[#2d2d30] border-b border-[#3e3e42] flex items-center px-4">
            <div className="flex items-center space-x-2 text-sm">
              <Code className="w-4 h-4 text-[#007acc]" />
              <span className="text-[#cccccc]">Guide</span>
            </div>
          </div>

          {/* Preview Content */}
          <div className="flex-1 p-6 overflow-auto">
            <div className="max-w-2xl">
              <div className="mb-6">
                <h2 className="text-2xl font-semibold text-[#cccccc] mb-2">
                  Welcome to AgentForge
                </h2>
                <p className="text-[#858585]">
                  AI-powered code generation made simple
                </p>
              </div>
              
              <div className="space-y-4 text-[#858585]">
                <p>
                  Describe your application in the editor using natural language. 
                  Be as detailed as possible for the best results.
                </p>

                <div className="bg-[#2d2d30] p-4 rounded border border-[#3e3e42]">
                  <h3 className="text-lg font-medium text-[#cccccc] mb-3">Tips for better results</h3>
                  <ul className="space-y-2 text-sm">
                    <li>• Specify the application type (Next.js, React, Vue, etc.)</li>
                    <li>• List key features and functionality</li>
                    <li>• Mention design preferences</li>
                    <li>• Include specific technologies or libraries</li>
                    <li>• Describe the target audience</li>
                  </ul>
                </div>

                <div className="bg-[#2d2d30] p-4 rounded border border-[#007acc]">
                  <h3 className="text-lg font-medium text-[#007acc] mb-3">How it works</h3>
                  <ol className="space-y-2 text-sm">
                    <li>1. AI analyzes your requirements</li>
                    <li>2. Generates complete project structure</li>
                    <li>3. Creates all necessary files and code</li>
                    <li>4. Provides live preview and editing</li>
                    <li>5. Allows real-time modifications</li>
                  </ol>
                </div>

                <div className="bg-[#2d2d30] p-4 rounded border border-[#3e3e42]">
                  <h3 className="text-lg font-medium text-[#cccccc] mb-3">Configuration</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>AI Provider:</span>
                      <span className="text-[#007acc]">Gemini (Free)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Model:</span>
                      <span className="text-[#cccccc]">gemini-1.5-flash</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <span className="text-[#007acc]">Ready</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
