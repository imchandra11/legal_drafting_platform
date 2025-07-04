import { useState, useEffect } from 'react';
import axios from 'axios';

export const useAISuggestions = (content) => {
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchSuggestions = async () => {
            if (!content || content.length < 50) return;
            
            try {
                setLoading(true);
                const response = await axios.post('/api/ai/suggest', { content });
                setSuggestions(response.data.suggestions);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        const timer = setTimeout(fetchSuggestions, 1000);
        return () => clearTimeout(timer);
    }, [content]);

    return [suggestions, loading, error];
};