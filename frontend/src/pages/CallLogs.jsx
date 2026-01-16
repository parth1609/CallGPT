import React, { useState, useMemo } from 'react';
import './CallLogs.css';

// SVG Icons
const SearchIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
);

const FilterIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
);

const PhoneIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
);

const CallLogs = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    // Dummy data for call logs
    const callLogsData = [
        { id: 1, callerNumber: '+1 (555) 123-4567', date: 'Jan 4, 2026 - 9:32 AM', duration: '2:45', callType: 'Inbound', status: 'Automated' },
        { id: 2, callerNumber: '+1 (555) 987-6543', date: 'Jan 4, 2026 - 9:28 AM', duration: '5:12', callType: 'Inbound', status: 'Transferred' },
        { id: 3, callerNumber: '+1 (555) 456-7890', date: 'Jan 4, 2026 - 9:15 AM', duration: '1:38', callType: 'Outbound', status: 'Completed' },
        { id: 4, callerNumber: '+1 (555) 321-0987', date: 'Jan 4, 2026 - 9:02 AM', duration: '3:21', callType: 'Inbound', status: 'Automated' },
        { id: 5, callerNumber: '+1 (555) 654-3210', date: 'Jan 4, 2026 - 8:55 AM', duration: '4:05', callType: 'Inbound', status: 'Transferred' },
        { id: 6, callerNumber: '+1 (555) 789-0123', date: 'Jan 4, 2026 - 8:42 AM', duration: '2:18', callType: 'Outbound', status: 'Completed' },
        { id: 7, callerNumber: '+1 (555) 234-5678', date: 'Jan 4, 2026 - 8:30 AM', duration: '6:45', callType: 'Inbound', status: 'Missed' },
        { id: 8, callerNumber: '+1 (555) 876-5432', date: 'Jan 4, 2026 - 8:15 AM', duration: '1:52', callType: 'Inbound', status: 'Automated' },
        { id: 9, callerNumber: '+1 (555) 345-6789', date: 'Jan 3, 2026 - 5:45 PM', duration: '3:33', callType: 'Outbound', status: 'Completed' },
        { id: 10, callerNumber: '+1 (555) 567-8901', date: 'Jan 3, 2026 - 4:20 PM', duration: '0:45', callType: 'Inbound', status: 'Missed' },
        { id: 11, callerNumber: '+1 (555) 890-1234', date: 'Jan 3, 2026 - 3:10 PM', duration: '4:28', callType: 'Inbound', status: 'Transferred' },
        { id: 12, callerNumber: '+1 (555) 012-3456', date: 'Jan 3, 2026 - 2:55 PM', duration: '2:15', callType: 'Inbound', status: 'Automated' },
    ];

    // Filter and search logic
    const filteredCalls = useMemo(() => {
        return callLogsData.filter(call => {
            const matchesSearch = call.callerNumber.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesStatus = statusFilter === 'all' || call.status.toLowerCase() === statusFilter.toLowerCase();
            return matchesSearch && matchesStatus;
        });
    }, [searchQuery, statusFilter]);

    // Statistics
    const stats = {
        total: callLogsData.length,
        automated: callLogsData.filter(c => c.status === 'Automated').length,
        transferred: callLogsData.filter(c => c.status === 'Transferred').length,
        missed: callLogsData.filter(c => c.status === 'Missed').length,
    };

    return (
        <div className="call-logs-page">
            {/* Header Section */}
            <div className="page-header">
                <div className="page-header-content">
                    <div className="page-header-icon">
                        <PhoneIcon />
                    </div>
                    <div>
                        <h1 className="page-title">Call Logs</h1>
                        <p className="page-subtitle">View and manage all your call history</p>
                    </div>
                </div>
            </div>

            {/* Stats Summary */}
            <div className="stats-summary">
                <div className="summary-item">
                    <span className="summary-value">{stats.total}</span>
                    <span className="summary-label">Total Calls</span>
                </div>
                <div className="summary-divider"></div>
                <div className="summary-item">
                    <span className="summary-value summary-automated">{stats.automated}</span>
                    <span className="summary-label">Automated</span>
                </div>
                <div className="summary-divider"></div>
                <div className="summary-item">
                    <span className="summary-value summary-transferred">{stats.transferred}</span>
                    <span className="summary-label">Transferred</span>
                </div>
                <div className="summary-divider"></div>
                <div className="summary-item">
                    <span className="summary-value summary-missed">{stats.missed}</span>
                    <span className="summary-label">Missed</span>
                </div>
            </div>

            {/* Filters Section */}
            <div className="filters-section">
                <div className="search-wrapper">
                    <span className="search-icon"><SearchIcon /></span>
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Search by phone number..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="filter-wrapper">
                    <span className="filter-icon"><FilterIcon /></span>
                    <select
                        className="filter-select"
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                    >
                        <option value="all">All Status</option>
                        <option value="automated">Automated</option>
                        <option value="transferred">Transferred</option>
                        <option value="completed">Completed</option>
                        <option value="missed">Missed</option>
                    </select>
                </div>
            </div>

            {/* Table Section */}
            <div className="table-card">
                <div className="table-wrapper">
                    <table className="logs-table">
                        <thead>
                            <tr>
                                <th>Caller Number</th>
                                <th>Date</th>
                                <th>Duration</th>
                                <th>Call Type</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredCalls.length > 0 ? (
                                filteredCalls.map((call) => (
                                    <tr key={call.id}>
                                        <td className="caller-cell">
                                            <span className="caller-icon"><PhoneIcon /></span>
                                            <span className="caller-number">{call.callerNumber}</span>
                                        </td>
                                        <td className="date-cell">{call.date}</td>
                                        <td className="duration-cell">{call.duration}</td>
                                        <td>
                                            <span className={`type-badge ${call.callType.toLowerCase()}`}>
                                                {call.callType}
                                            </span>
                                        </td>
                                        <td>
                                            <span className={`status-badge ${call.status.toLowerCase()}`}>
                                                {call.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="5" className="no-results">
                                        <div className="no-results-content">
                                            <SearchIcon />
                                            <p>No calls found matching your criteria</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Table Footer */}
                <div className="table-footer">
                    <span className="results-count">
                        Showing {filteredCalls.length} of {callLogsData.length} calls
                    </span>
                </div>
            </div>
        </div>
    );
};

export default CallLogs;
