"use client";

import { useState } from 'react';
import { AppGenForm } from '../components/AppGenForm';
import IDEWithNoSSR from '../components/IDE'; // Corrected import path

export default function Home() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [prompt, setPrompt] = useState('');

  const handleFormSubmit = (newPrompt: string) => {
    setPrompt(newPrompt);
    setIsGenerating(true);
  };

  return (
    <div>
      {!isGenerating ? (
        <AppGenForm onSubmit={handleFormSubmit} />
      ) : (
        <IDEWithNoSSR prompt={prompt} />
      )}
    </div>
  );
}
