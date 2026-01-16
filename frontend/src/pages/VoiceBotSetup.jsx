import React, { useState } from 'react';
import './VoiceBotSetup.css';

// SVG Icons
const BotIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="10" rx="2" />
        <circle cx="12" cy="5" r="2" />
        <path d="M12 7v4" />
        <line x1="8" y1="16" x2="8" y2="16" />
        <line x1="16" y1="16" x2="16" y2="16" />
    </svg>
);

const SaveIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
        <polyline points="17 21 17 13 7 13 7 21" />
        <polyline points="7 3 7 8 15 8" />
    </svg>
);

const LanguageIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
);

const MessageIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
);

const PhoneIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
);

const CheckIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
    </svg>
);

const VoiceBotSetup = () => {
    const [formData, setFormData] = useState({
        botName: 'CallGPT Assistant',
        language: 'en-US',
        greetingMessage: 'Hello! Thank you for calling. How can I assist you today?',
        forwardNumber: '+1 (555) 000-0000',
    });

    const [botEnabled, setBotEnabled] = useState(true);
    const [saved, setSaved] = useState(false);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        setSaved(false);
    };

    const handleToggle = () => {
        setBotEnabled(!botEnabled);
        setSaved(false);
    };

    const handleSave = () => {
        // Simulate save action
        console.log('Saving configuration:', { ...formData, botEnabled });
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
    };

    const languages = [
        { code: 'en-US', name: 'English (US)' },
        { code: 'en-GB', name: 'English (UK)' },
        { code: 'es-ES', name: 'Spanish' },
        { code: 'fr-FR', name: 'French' },
        { code: 'de-DE', name: 'German' },
        { code: 'it-IT', name: 'Italian' },
        { code: 'pt-BR', name: 'Portuguese (Brazil)' },
        { code: 'ja-JP', name: 'Japanese' },
        { code: 'zh-CN', name: 'Chinese (Simplified)' },
        { code: 'hi-IN', name: 'Hindi' },
    ];

    return (
        <div className="voice-bot-setup">
            {/* Header Section */}
            <div className="page-header">
                <div className="page-header-content">
                    <div className="page-header-icon">
                        <BotIcon />
                    </div>
                    <div>
                        <h1 className="page-title">Voice Bot Setup</h1>
                        <p className="page-subtitle">Configure your voice assistant settings</p>
                    </div>
                </div>
            </div>

            {/* Configuration Panel */}
            <div className="config-panel">
                {/* Status Card */}
                <div className={`status-card ${botEnabled ? 'enabled' : 'disabled'}`}>
                    <div className="status-info">
                        <div className="status-icon-wrapper">
                            <BotIcon />
                        </div>
                        <div className="status-text">
                            <h3>Voice Bot Status</h3>
                            <p>{botEnabled ? 'Your bot is currently active and handling calls' : 'Your bot is disabled and not receiving calls'}</p>
                        </div>
                    </div>
                    <div className="toggle-wrapper">
                        <span className="toggle-label">{botEnabled ? 'Enabled' : 'Disabled'}</span>
                        <button
                            className={`toggle-button ${botEnabled ? 'active' : ''}`}
                            onClick={handleToggle}
                            aria-label="Toggle bot status"
                        >
                            <span className="toggle-slider"></span>
                        </button>
                    </div>
                </div>

                {/* Form Section */}
                <div className="form-card">
                    <div className="form-header">
                        <h2>Bot Configuration</h2>
                        <p>Customize your voice assistant behavior</p>
                    </div>

                    <div className="form-grid">
                        {/* Bot Name */}
                        <div className="form-group">
                            <label className="form-label">
                                <span className="label-icon"><BotIcon /></span>
                                Bot Name
                            </label>
                            <input
                                type="text"
                                name="botName"
                                className="form-input"
                                placeholder="Enter bot name"
                                value={formData.botName}
                                onChange={handleInputChange}
                            />
                            <span className="form-hint">This name will be used to identify your bot</span>
                        </div>

                        {/* Language */}
                        <div className="form-group">
                            <label className="form-label">
                                <span className="label-icon"><LanguageIcon /></span>
                                Language
                            </label>
                            <select
                                name="language"
                                className="form-select"
                                value={formData.language}
                                onChange={handleInputChange}
                            >
                                {languages.map(lang => (
                                    <option key={lang.code} value={lang.code}>
                                        {lang.name}
                                    </option>
                                ))}
                            </select>
                            <span className="form-hint">Select the primary language for voice interactions</span>
                        </div>

                        {/* Greeting Message */}
                        <div className="form-group full-width">
                            <label className="form-label">
                                <span className="label-icon"><MessageIcon /></span>
                                Greeting Message
                            </label>
                            <textarea
                                name="greetingMessage"
                                className="form-textarea"
                                placeholder="Enter the greeting message your bot will say..."
                                rows="4"
                                value={formData.greetingMessage}
                                onChange={handleInputChange}
                            />
                            <span className="form-hint">This message plays when someone calls</span>
                        </div>

                        {/* Forward Call Number */}
                        <div className="form-group">
                            <label className="form-label">
                                <span className="label-icon"><PhoneIcon /></span>
                                Forward Call Number
                            </label>
                            <input
                                type="tel"
                                name="forwardNumber"
                                className="form-input"
                                placeholder="+1 (555) 000-0000"
                                value={formData.forwardNumber}
                                onChange={handleInputChange}
                            />
                            <span className="form-hint">Calls will be forwarded to this number when needed</span>
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="form-actions">
                        <button
                            className={`save-button ${saved ? 'saved' : ''}`}
                            onClick={handleSave}
                        >
                            {saved ? (
                                <>
                                    <CheckIcon />
                                    <span>Saved Successfully</span>
                                </>
                            ) : (
                                <>
                                    <SaveIcon />
                                    <span>Save Configuration</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Tips Card */}
                <div className="tips-card">
                    <h3>💡 Pro Tips</h3>
                    <ul className="tips-list">
                        <li>Keep your greeting message short and welcoming</li>
                        <li>Test your bot regularly to ensure quality responses</li>
                        <li>Use the forward number for complex queries that need human assistance</li>
                        <li>Update your FAQs to improve automated responses</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default VoiceBotSetup;
