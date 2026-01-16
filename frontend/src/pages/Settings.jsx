import React, { useState } from 'react';
import './Settings.css';

// SVG Icons
const SettingsIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
);

const CpuIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
        <rect x="9" y="9" width="6" height="6" />
        <line x1="9" y1="1" x2="9" y2="4" />
        <line x1="15" y1="1" x2="15" y2="4" />
        <line x1="9" y1="20" x2="9" y2="23" />
        <line x1="15" y1="20" x2="15" y2="23" />
        <line x1="20" y1="9" x2="23" y2="9" />
        <line x1="20" y1="14" x2="23" y2="14" />
        <line x1="1" y1="9" x2="4" y2="9" />
        <line x1="1" y1="14" x2="4" y2="14" />
    </svg>
);

const LayersIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 2 7 12 12 22 7 12 2" />
        <polyline points="2 17 12 22 22 17" />
        <polyline points="2 12 12 17 22 12" />
    </svg>
);

const SearchIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
);

const DatabaseIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
);

const SaveIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
        <polyline points="17 21 17 13 7 13 7 21" />
        <polyline points="7 3 7 8 15 8" />
    </svg>
);

const CheckIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
    </svg>
);

const InfoIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="16" x2="12" y2="12" />
        <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
);

const Settings = () => {
    // Model Configuration State
    const [llmModel, setLlmModel] = useState('openai/gpt-oss-120b');
    const [temperature, setTemperature] = useState(0.5);

    // Embeddings State
    const [embeddingsModel, setEmbeddingsModel] = useState('sentence-transformers/all-MiniLM-L6-v2');

    // Search Configuration State
    const [searchType, setSearchType] = useState('mmr');
    const [topK, setTopK] = useState(4);
    const [fetchK, setFetchK] = useState(20);
    const [lambda, setLambda] = useState(0.5);

    // Supabase Configuration State
    const [supabaseTable, setSupabaseTable] = useState('documents');
    const [supabaseRpc, setSupabaseRpc] = useState('match_documents');

    // Toast State
    const [showToast, setShowToast] = useState(false);

    const handleSave = () => {
        const settings = {
            modelConfiguration: {
                llmModel,
                temperature,
            },
            embeddings: {
                embeddingsModel,
            },
            searchConfiguration: {
                searchType,
                topK,
                fetchK,
                lambda,
            },
            supabaseConfiguration: {
                supabaseTable,
                supabaseRpc,
            },
        };

        console.log('Settings saved:', settings);

        // Show toast
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
    };

    return (
        <div className="settings">
            {/* Header Section */}
            <div className="settings-header">
                <div className="settings-header-content">
                    <h1 className="settings-title">
                        <SettingsIcon />
                        Settings
                    </h1>
                    <p className="settings-subtitle">
                        Configure your voice assistant's AI models, search parameters, and database connections.
                    </p>
                </div>
            </div>

            {/* Settings Grid */}
            <div className="settings-grid">
                {/* Model Configuration Card */}
                <div className="settings-card">
                    <div className="card-icon model">
                        <CpuIcon />
                    </div>
                    <h2 className="card-title">
                        Model Configuration
                        <span className="card-title-badge">AI</span>
                    </h2>

                    <div className="form-group">
                        <label className="form-label">
                            LLM Model
                            <span className="form-label-hint">(OpenRouter compatible)</span>
                        </label>
                        <input
                            type="text"
                            className="text-input"
                            value={llmModel}
                            onChange={(e) => setLlmModel(e.target.value)}
                            placeholder="Enter model name..."
                        />
                    </div>

                    <div className="form-group">
                        <div className="slider-container">
                            <div className="slider-header">
                                <label className="form-label">Temperature</label>
                                <span className="slider-value">{temperature.toFixed(1)}</span>
                            </div>
                            <div className="slider-wrapper">
                                <input
                                    type="range"
                                    className="slider"
                                    min="0"
                                    max="1"
                                    step="0.1"
                                    value={temperature}
                                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                                />
                            </div>
                            <div className="slider-labels">
                                <span>0.0 (Precise)</span>
                                <span>1.0 (Creative)</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Embeddings Card */}
                <div className="settings-card">
                    <div className="card-icon embeddings">
                        <LayersIcon />
                    </div>
                    <h2 className="card-title">
                        Embeddings
                        <span className="card-title-badge">Vector</span>
                    </h2>

                    <div className="form-group">
                        <label className="form-label">
                            Embeddings Model
                            <span className="form-label-hint">(Sentence Transformers)</span>
                        </label>
                        <input
                            type="text"
                            className="text-input"
                            value={embeddingsModel}
                            onChange={(e) => setEmbeddingsModel(e.target.value)}
                            placeholder="Enter embeddings model..."
                        />
                        <div className="info-badge">
                            <InfoIcon />
                            Used for semantic similarity search
                        </div>
                    </div>
                </div>

                {/* Search Configuration Card */}
                <div className="settings-card">
                    <div className="card-icon search">
                        <SearchIcon />
                    </div>
                    <h2 className="card-title">
                        Search Configuration
                        <span className="card-title-badge">RAG</span>
                    </h2>

                    <div className="form-group">
                        <label className="form-label">Search Type</label>
                        <div className="radio-group">
                            <div className="radio-option">
                                <input
                                    type="radio"
                                    id="mmr"
                                    name="searchType"
                                    className="radio-input"
                                    value="mmr"
                                    checked={searchType === 'mmr'}
                                    onChange={(e) => setSearchType(e.target.value)}
                                />
                                <label htmlFor="mmr" className="radio-label">MMR</label>
                            </div>
                            <div className="radio-option">
                                <input
                                    type="radio"
                                    id="similarity"
                                    name="searchType"
                                    className="radio-input"
                                    value="similarity"
                                    checked={searchType === 'similarity'}
                                    onChange={(e) => setSearchType(e.target.value)}
                                />
                                <label htmlFor="similarity" className="radio-label">Similarity</label>
                            </div>
                        </div>
                    </div>

                    <div className="settings-divider"></div>

                    <div className="form-group">
                        <div className="slider-container">
                            <div className="slider-header">
                                <label className="form-label">Top-K</label>
                                <span className="slider-value">{topK}</span>
                            </div>
                            <div className="slider-wrapper">
                                <input
                                    type="range"
                                    className="slider"
                                    min="1"
                                    max="10"
                                    step="1"
                                    value={topK}
                                    onChange={(e) => setTopK(parseInt(e.target.value))}
                                />
                            </div>
                            <div className="slider-labels">
                                <span>1</span>
                                <span>10</span>
                            </div>
                        </div>
                    </div>

                    <div className="form-group">
                        <div className="slider-container">
                            <div className="slider-header">
                                <label className="form-label">Fetch-K (MMR)</label>
                                <span className="slider-value">{fetchK}</span>
                            </div>
                            <div className="slider-wrapper">
                                <input
                                    type="range"
                                    className="slider"
                                    min="5"
                                    max="50"
                                    step="1"
                                    value={fetchK}
                                    onChange={(e) => setFetchK(parseInt(e.target.value))}
                                />
                            </div>
                            <div className="slider-labels">
                                <span>5</span>
                                <span>50</span>
                            </div>
                        </div>
                    </div>

                    <div className="form-group">
                        <div className="slider-container">
                            <div className="slider-header">
                                <label className="form-label">Lambda (MMR)</label>
                                <span className="slider-value">{lambda.toFixed(2)}</span>
                            </div>
                            <div className="slider-wrapper">
                                <input
                                    type="range"
                                    className="slider"
                                    min="0"
                                    max="1"
                                    step="0.05"
                                    value={lambda}
                                    onChange={(e) => setLambda(parseFloat(e.target.value))}
                                />
                            </div>
                            <div className="slider-labels">
                                <span>0.0 (Diversity)</span>
                                <span>1.0 (Relevance)</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Supabase Configuration Card */}
                <div className="settings-card">
                    <div className="card-icon supabase">
                        <DatabaseIcon />
                    </div>
                    <h2 className="card-title">
                        Supabase Configuration
                        <span className="card-title-badge">Database</span>
                    </h2>

                    <div className="form-group">
                        <label className="form-label">Supabase Table Name</label>
                        <input
                            type="text"
                            className="text-input"
                            value={supabaseTable}
                            onChange={(e) => setSupabaseTable(e.target.value)}
                            placeholder="Enter table name..."
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Supabase RPC Query</label>
                        <input
                            type="text"
                            className="text-input"
                            value={supabaseRpc}
                            onChange={(e) => setSupabaseRpc(e.target.value)}
                            placeholder="Enter RPC function name..."
                        />
                        <div className="info-badge">
                            <InfoIcon />
                            PostgreSQL function for vector search
                        </div>
                    </div>
                </div>
            </div>

            {/* Save Button */}
            <div className="save-button-container">
                <button className="save-button" onClick={handleSave}>
                    <span className="save-button-icon">
                        <SaveIcon />
                    </span>
                    Save Settings
                </button>
            </div>

            {/* Success Toast */}
            {showToast && (
                <div className="toast">
                    <CheckIcon />
                    Settings saved successfully!
                </div>
            )}
        </div>
    );
};

export default Settings;
