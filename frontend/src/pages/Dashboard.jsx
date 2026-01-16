import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

// SVG Icons
const PhoneIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
);

const PercentIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="19" y1="5" x2="5" y2="19" />
        <circle cx="6.5" cy="6.5" r="2.5" />
        <circle cx="17.5" cy="17.5" r="2.5" />
    </svg>
);

const BotIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="10" rx="2" />
        <circle cx="12" cy="5" r="2" />
        <path d="M12 7v4" />
        <line x1="8" y1="16" x2="8" y2="16" />
        <line x1="16" y1="16" x2="16" y2="16" />
    </svg>
);

const ClockIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
    </svg>
);

const HeadsetIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 18v-6a9 9 0 0 1 18 0v6" />
        <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z" />
    </svg>
);

const ScriptIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
);

const FAQIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
);

const AnalyticsIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
);

const TestIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
);

const Dashboard = () => {
    const navigate = useNavigate();

    const stats = [
        {
            title: 'Total Calls Today',
            value: '472',
            icon: <PhoneIcon />,
            color: 'blue',
            trend: '+12%'
        },
        {
            title: 'Automation Rate',
            value: '32%',
            icon: <PercentIcon />,
            color: 'green',
            trend: '+5%'
        },
        {
            title: 'Active Bots',
            value: '2',
            icon: <BotIcon />,
            color: 'purple',
            trend: 'Active'
        },
        {
            title: 'Saved Agent Hours',
            value: '128',
            icon: <ClockIcon />,
            color: 'orange',
            trend: '+18h'
        },
    ];

    const recentCalls = [
        { callerNumber: '+1 (555) 123-4567', dateTime: 'Jan 4, 2026 - 9:32 AM', duration: '2:45', status: 'Automated' },
        { callerNumber: '+1 (555) 987-6543', dateTime: 'Jan 4, 2026 - 9:28 AM', duration: '5:12', status: 'Transferred' },
        { callerNumber: '+1 (555) 456-7890', dateTime: 'Jan 4, 2026 - 9:15 AM', duration: '1:38', status: 'Automated' },
        { callerNumber: '+1 (555) 321-0987', dateTime: 'Jan 4, 2026 - 9:02 AM', duration: '3:21', status: 'Automated' },
        { callerNumber: '+1 (555) 654-3210', dateTime: 'Jan 4, 2026 - 8:55 AM', duration: '4:05', status: 'Transferred' },
    ];

    const quickActions = [
        { label: 'Create Bot Script', icon: <ScriptIcon />, path: '/voice-bot-setup' },
        { label: 'Add FAQ Reply', icon: <FAQIcon />, path: '/faqs' },
        { label: 'Open Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
        { label: 'Test Voice Assistant', icon: <TestIcon />, path: '/voice-bot-setup' },
    ];

    return (
        <div className="dashboard">
            {/* Header Section */}
            <div className="dashboard-header">
                <div className="dashboard-header-content">
                    <h1 className="dashboard-title">Dashboard Overview</h1>
                    <p className="dashboard-subtitle">Welcome back! Here's what's happening with your voice assistant today.</p>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="stats-grid">
                {stats.map((stat, index) => (
                    <div key={index} className={`stat-card stat-card-${stat.color}`}>
                        <div className="stat-icon-wrapper">
                            <div className={`stat-icon stat-icon-${stat.color}`}>
                                {stat.icon}
                            </div>
                        </div>
                        <div className="stat-content">
                            <span className="stat-value">{stat.value}</span>
                            <span className="stat-title">{stat.title}</span>
                        </div>
                        <div className={`stat-trend stat-trend-${stat.color}`}>
                            {stat.trend}
                        </div>
                    </div>
                ))}
            </div>

            {/* Voice Assistant Status */}
            <div className="voice-status-card">
                <div className="voice-status-icon">
                    <HeadsetIcon />
                    <div className="pulse-ring"></div>
                </div>
                <div className="voice-status-content">
                    <h3 className="voice-status-title">Your Voice Assistant is Active</h3>
                    <p className="voice-status-subtitle">Monitoring and responding to calls in real-time.</p>
                </div>
                <div className="voice-status-indicator">
                    <span className="status-dot"></span>
                    <span className="status-text">Online</span>
                </div>
            </div>

            {/* Main Content Grid */}
            <div className="dashboard-grid">
                {/* Recent Calls Table */}
                <div className="recent-calls-card">
                    <div className="card-header">
                        <h2 className="card-title">Recent Calls</h2>
                        <button className="view-all-btn" onClick={() => navigate('/call-logs')}>
                            View All
                        </button>
                    </div>
                    <div className="table-wrapper">
                        <table className="calls-table">
                            <thead>
                                <tr>
                                    <th>Caller Number</th>
                                    <th>Date & Time</th>
                                    <th>Duration</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recentCalls.map((call, index) => (
                                    <tr key={index}>
                                        <td className="caller-number">{call.callerNumber}</td>
                                        <td className="call-datetime">{call.dateTime}</td>
                                        <td className="call-duration">{call.duration}</td>
                                        <td>
                                            <span className={`status-badge ${call.status.toLowerCase()}`}>
                                                {call.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="quick-actions-card">
                    <div className="card-header">
                        <h2 className="card-title">Quick Actions</h2>
                    </div>
                    <div className="quick-actions-grid">
                        {quickActions.map((action, index) => (
                            <button
                                key={index}
                                className="quick-action-btn"
                                onClick={() => navigate(action.path)}
                            >
                                <span className="quick-action-icon">{action.icon}</span>
                                <span className="quick-action-label">{action.label}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
