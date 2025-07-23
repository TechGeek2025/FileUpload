import React, { useState } from 'react';

const DataVisualization = () => {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [images, setImages] = useState([]);
    
    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        setLoading(true);
        setImages([]); // Clear previous images
        
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64 = e.target.result.split(',')[1];
            
            const payload = {
                prompt: "Create comprehensive data visualizations",
                file_name: file.name,
                file_content: base64,
                file_type: file.type,
                analysis_type: "comprehensive"
            };
            
            try {
                const response = await fetch('/visualize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                setResult(data);
                
                // 🎯 Auto-fetch and display images
                if (data.success && data.generated_files) {
                    const imageFiles = data.generated_files.filter(
                        file => file.file_type === 'image'
                    );
                    
                    // Fetch each image and create blob URLs
                    const imagePromises = imageFiles.map(async (fileInfo) => {
                        const imageResponse = await fetch(fileInfo.download_url);
                        const blob = await imageResponse.blob();
                        const imageUrl = URL.createObjectURL(blob);
                        
                        return {
                            name: fileInfo.name,
                            url: imageUrl,
                            size: fileInfo.size_bytes
                        };
                    });
                    
                    const fetchedImages = await Promise.all(imagePromises);
                    setImages(fetchedImages);
                }
                
            } catch (error) {
                console.error('Error:', error);
            } finally {
                setLoading(false);
            }
        };
        
        reader.readAsDataURL(file);
    };
    
    return (
        <div>
            <input 
                type="file" 
                onChange={handleFileUpload} 
                accept=".csv,.xlsx,.json" 
            />
            
            {loading && <div>🔄 Analyzing data and generating charts...</div>}
            
            {result && result.success && (
                <div>
                    <h3>📊 Analysis Results</h3>
                    <p>⏱️ Completed in {result.execution_time.toFixed(2)}s</p>
                    
                    {/* 🖼️ Display Images Inline */}
                    {images.length > 0 && (
                        <div>
                            <h4>📈 Generated Charts:</h4>
                            <div style={{ display: 'grid', gap: '20px' }}>
                                {images.map((image, index) => (
                                    <div key={index} style={{ border: '1px solid #ddd', padding: '10px' }}>
                                        <h5>{image.name}</h5>
                                        <img 
                                            src={image.url} 
                                            alt={image.name}
                                            style={{ 
                                                maxWidth: '100%', 
                                                height: 'auto',
                                                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                                            }}
                                        />
                                        <p>Size: {(image.size / 1024).toFixed(1)} KB</p>
                                        
                                        {/* Download button */}
                                        <a 
                                            href={image.url} 
                                            download={image.name}
                                            style={{ 
                                                display: 'inline-block',
                                                padding: '5px 10px',
                                                background: '#007bff',
                                                color: 'white',
                                                textDecoration: 'none',
                                                borderRadius: '3px'
                                            }}
                                        >
                                            💾 Download
                                        </a>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    {/* 📝 Analysis Text */}
                    <div style={{ marginTop: '20px' }}>
                        <h4>🔍 Analysis:</h4>
                        <div style={{ 
                            background: '#f8f9fa', 
                            padding: '15px', 
                            borderRadius: '5px',
                            whiteSpace: 'pre-wrap'
                        }}>
                            {result.response_text}
                        </div>
                    </div>
                </div>
            )}
            
            {result && !result.success && (
                <div style={{ color: 'red' }}>
                    ❌ Error: {result.response_text}
                </div>
            )}
        </div>
    );
};

export default DataVisualization;
