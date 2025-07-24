import { useState, useEffect, useRef } from 'react';

const useBedrockSSE = () => {
    const [streamingText, setStreamingText] = useState('');
    const [generatedCharts, setGeneratedCharts] = useState([]);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [status, setStatus] = useState('');
    const [error, setError] = useState(null);
    const eventSourceRef = useRef(null);

    const startAnalysis = async (file, prompt) => {
        if (!file) return;

        // Clear previous results
        setStreamingText('');
        setGeneratedCharts([]);
        setError(null);
        setStatus('');
        setIsAnalyzing(true);

        // Convert file to base64
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64Data = e.target.result.split(',')[1];

            try {
                // Close existing EventSource if any
                if (eventSourceRef.current) {
                    eventSourceRef.current.close();
                }

                // Make POST request to start streaming
                const response = await fetch('http://localhost:8000/analyze-file-stream', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        file_data: base64Data,
                        file_name: file.name,
                        file_type: file.type,
                        prompt: prompt
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to start analysis');
                }

                // Create EventSource from the response
                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                const processStream = async () => {
                    try {
                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;

                            const chunk = decoder.decode(value);
                            const lines = chunk.split('\n');

                            for (const line of lines) {
                                if (line.startsWith('event:')) {
                                    const eventType = line.substring(6).trim();
                                    continue;
                                }
                                
                                if (line.startsWith('data:')) {
                                    const data = line.substring(5).trim();
                                    if (!data) continue;

                                    try {
                                        const parsedData = JSON.parse(data);
                                        handleSSEMessage(eventType, parsedData);
                                    } catch (e) {
                                        console.error('Failed to parse SSE data:', e);
                                    }
                                }
                            }
                        }
                    } catch (error) {
                        console.error('Stream reading error:', error);
                        setError('Stream connection lost');
                        setIsAnalyzing(false);
                    }
                };

                processStream();

            } catch (error) {
                console.error('Failed to start analysis:', error);
                setError(error.message);
                setIsAnalyzing(false);
            }
        };

        reader.readAsDataURL(file);
    };

    const handleSSEMessage = (eventType, data) => {
        switch (eventType) {
            case 'text':
                setStreamingText(prev => prev + data.content);
                break;
                
            case 'chart':
                setGeneratedCharts(prev => [...prev, {
                    filename: data.filename,
                    data: data.data,
                    type: data.type,
                    size: data.size
                }]);
                break;
                
            case 'status':
                setStatus(data.message);
                break;
                
            case 'complete':
                setIsAnalyzing(false);
                setStatus(data.message);
                break;
                
            case 'error':
                setError(data.error);
                setIsAnalyzing(false);
                break;
        }
    };

    const stopAnalysis = () => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
        setIsAnalyzing(false);
    };

    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    return {
        streamingText,
        generatedCharts,
        isAnalyzing,
        status,
        error,
        startAnalysis,
        stopAnalysis
    };
};

export default useBedrockSSE;
