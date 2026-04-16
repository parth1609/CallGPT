import React, { useState } from 'react';
import './DocumentUpload.css';

const DocumentUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');

  // Configuration state
  const [config, setConfig] = useState({
    bucketName: 'openai-bucket',
    chunkSize: 1000,
    chunkOverlap: 200,
    embeddingsModel: 'sentence-transformers/all-MiniLM-L6-v2',
    rebuildIndex: false
  });

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Check API health on component mount
  React.useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/pipeline/health`, {
        method: 'GET',
        timeout: 2000
      });
      
      if (response.ok) {
        setApiStatus('connected');
      } else {
        setApiStatus('error');
      }
    } catch (err) {
      setApiStatus('offline');
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Only accept text files
      if (file.type !== 'text/plain') {
        setError('Please upload a text file (.txt)');
        return;
      }
      setSelectedFile(file);
      setError(null);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Build query parameters
      const params = new URLSearchParams({
        bucket_name: config.bucketName,
        embeddings_model: config.embeddingsModel,
        chunk_size: config.chunkSize.toString(),
        chunk_overlap: config.chunkOverlap.toString()
      });

      const response = await fetch(
        `${API_BASE_URL}/api/v1/pipeline/organisations/upload-file?${params}`,
        {
          method: 'POST',
          body: formData,
          timeout: 300000 // 5 minutes timeout
        }
      );

      const result = await response.json();

      if (response.status === 201) {
        setUploadResult(result);
      } else {
        setError(result.detail || 'Upload failed');
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request timed out. The file might be too large or processing is taking too long.');
      } else if (err.message.includes('Failed to fetch')) {
        setError('Could not connect to API server. Please ensure the FastAPI server is running.');
      } else {
        setError(`Error uploading document: ${err.message}`);
      }
    } finally {
      setUploading(false);
    }
  };

  const getApiStatusIndicator = () => {
    switch (apiStatus) {
      case 'connected':
        return <span className="status-indicator success">✅ API Connected</span>;
      case 'error':
        return <span className="status-indicator warning">⚠️ API Not Responding</span>;
      case 'offline':
        return <span className="status-indicator error">❌ API Offline</span>;
      default:
        return <span className="status-indicator checking">🔄 Checking...</span>;
    }
  };

  return (
    <div className="document-upload">
      <div className="upload-header">
        <h2>📄 Organization</h2>
        <p>Upload and index your organization's documents</p>
      </div>

      <div className="api-status">
        {getApiStatusIndicator()}
        {apiStatus !== 'connected' && (
          <span className="api-url">URL: {API_BASE_URL}</span>
        )}
      </div>

      <div className="upload-container">
        <div className="config-panel">
          <h3>⚙️ Org Configuration</h3>
          
          <div className="config-group">
            <label htmlFor="bucketName">Bucket/Index Name</label>
            <input
              id="bucketName"
              type="text"
              value={config.bucketName}
              onChange={(e) => setConfig({...config, bucketName: e.target.value})}
            />
          </div>

          <div className="config-group">
            <label htmlFor="chunkSize">Chunk Size: {config.chunkSize} chars</label>
            <input
              id="chunkSize"
              type="range"
              min="500"
              max="2000"
              step="100"
              value={config.chunkSize}
              onChange={(e) => setConfig({...config, chunkSize: parseInt(e.target.value)})}
            />
          </div>

          <div className="config-group">
            <label htmlFor="chunkOverlap">Chunk Overlap: {config.chunkOverlap} chars</label>
            <input
              id="chunkOverlap"
              type="range"
              min="0"
              max="500"
              step="50"
              value={config.chunkOverlap}
              onChange={(e) => setConfig({...config, chunkOverlap: parseInt(e.target.value)})}
            />
          </div>

          <div className="config-group">
            <label htmlFor="embeddingsModel">Embeddings Model</label>
            <input
              id="embeddingsModel"
              type="text"
              value={config.embeddingsModel}
              onChange={(e) => setConfig({...config, embeddingsModel: e.target.value})}
            />
          </div>

          <div className="config-group">
            <label>
              <input
                type="checkbox"
                checked={config.rebuildIndex}
                onChange={(e) => setConfig({...config, rebuildIndex: e.target.checked})}
              />
              Rebuild Index
            </label>
          </div>
        </div>

        <div className="upload-panel">
          <div className="file-upload-area">
            <input
              type="file"
              id="fileInput"
              accept=".txt"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            <label htmlFor="fileInput" className="file-upload-label">
              📁 Choose a text file to upload
            </label>
            <p className="upload-help">Upload text documents to be indexed</p>
          </div>

          {selectedFile && (
            <div className="file-info">
              <div className="file-details">
                <h4>📄 File Information</h4>
                <p><strong>Name:</strong> {selectedFile.name}</p>
                <p><strong>Size:</strong> {selectedFile.size} bytes</p>
              </div>
              
              <button
                className="upload-button"
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading ? '⏳ Processing...' : '🚀 Process and Index Document'}
              </button>
            </div>
          )}

          {!selectedFile && (
            <div className="upload-prompt">
              <p>👆 Please upload a text file to begin processing</p>
            </div>
          )}

          {uploading && (
            <div className="upload-progress">
              <div className="spinner"></div>
              <p>Processing document... This may take a moment.</p>
            </div>
          )}

          {error && (
            <div className="error-message">
              <h4>❌ Error</h4>
              <p>{error}</p>
            </div>
          )}

          {uploadResult && (
            <div className="success-message">
              <h4>✅ Document processed and indexed successfully!</h4>
              
              <div className="result-details">
                <h5>📊 Processing Details</h5>
                <div className="detail-grid">
                  <div className="detail-item">
                    <strong>Status:</strong> {uploadResult.status || 'N/A'}
                  </div>
                  <div className="detail-item">
                    <strong>Message:</strong> {uploadResult.message || 'N/A'}
                  </div>
                  <div className="detail-item">
                    <strong>Filename:</strong> {uploadResult.filename || 'N/A'}
                  </div>
                  <div className="detail-item">
                    <strong>Bucket/Index:</strong> {uploadResult.bucket_name || 'N/A'}
                  </div>
                  <div className="detail-item">
                    <strong>Chunks created:</strong> {uploadResult.chunks_created || 0}
                  </div>
                </div>
                
                {uploadResult.metadata && (
                  <div className="metadata-section">
                    <h5>Metadata:</h5>
                    <pre className="metadata-json">
                      {JSON.stringify(uploadResult.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="metrics-panel">
        <h3>Current Configuration</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <h4>Bucket/Index</h4>
            <p>{config.bucketName}</p>
          </div>
          <div className="metric-card">
            <h4>Chunk Size</h4>
            <p>{config.chunkSize} chars</p>
          </div>
          <div className="metric-card">
            <h4>Chunk Overlap</h4>
            <p>{config.chunkOverlap} chars</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
