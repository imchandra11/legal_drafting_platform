import React from 'react';
import { useAISuggestions } from '../../hooks/useAISuggestions';

const SmartEditor = ({ content, onContentChange }) => {
    const [suggestions, loading, error] = useAISuggestions(content);
    
    const handleAccept = (suggestion) => {
        const newContent = applySuggestion(content, suggestion);
        onContentChange(newContent);
    };

    const applySuggestion = (text, suggestion) => {
        return text.replace(
            suggestion.context, 
            suggestion.replacement
        );
    };

    return (
        <div className="editor-container">
            <textarea
                value={content}
                onChange={(e) => onContentChange(e.target.value)}
                className="w-full h-64 p-4 border rounded"
            />
            
            <div className="suggestions-panel mt-4">
                <h3 className="text-lg font-semibold mb-2">AI Suggestions</h3>
                
                {loading && <p>Loading suggestions...</p>}
                {error && <p className="text-red-500">Error: {error}</p>}
                
                {suggestions.map((suggestion, index) => (
                    <div key={index} className="suggestion-card p-3 mb-2 border rounded">
                        <p className="suggestion-reason">{suggestion.reason}</p>
                        <div className="suggestion-content bg-yellow-50 p-2 my-2">
                            {suggestion.replacement}
                        </div>
                        <button 
                            onClick={() => handleAccept(suggestion)}
                            className="bg-blue-500 text-white px-3 py-1 rounded"
                        >
                            Apply
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SmartEditor;