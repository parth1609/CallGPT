import React, { useState } from 'react';
import './Analytics.css';

// SVG Icons
const PhoneIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
);

const BotIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="10" rx="2" />
        <circle cx="12" cy="5" r="2" />
        <path d="M12 7v4" />
        <line x1="8" y1="16" x2="8" y2="16" />
        <line x1="16" y1="16" x2="16" y2="16" />
    </svg>
);

const TransferIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M16 3h5v5" />
        <path d="M21 3l-7 7" />
        <path d="M21 14v7H3V3h7" />
    </svg>
);

const TrendUpIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
        <polyline points="17 6 23 6 23 12" />
    </svg>
);

const TrendDownIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
        <polyline points="17 18 23 18 23 12" />
    </svg>
);

const ClockIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
    </svg>
);

const StarIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
);

const ZapIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
);

const CheckCircleIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
);

const Analytics = () => {
    const [selectedRange, setSelectedRange] = useState('7days');

    const dateRanges = [
        { id: 'today', label: 'Today' },
        { id: '7days', label: '7 Days' },
        { id: '30days', label: '30 Days' },
        { id: '90days', label: '90 Days' },
    ];

    const metrics = [
        {
            id: 'total',
            label: 'Total Calls',
            value: '2,847',
            trend: '+12.5%',
            trendDirection: 'up',
            description: 'vs previous period',
            icon: <PhoneIcon />,
            miniChartData: [60, 45, 80, 55, 75, 90, 85],
        },
        {
            id: 'automated',
            label: 'Automated Calls',
            value: '2,134',
            trend: '+18.2%',
            trendDirection: 'up',
            description: '74.9% automation rate',
            icon: <BotIcon />,
            miniChartData: [40, 55, 70, 65, 80, 85, 95],
        },
        {
            id: 'transfers',
            label: 'Human Transfers',
            value: '713',
            trend: '-8.4%',
            trendDirection: 'down',
            description: '25.1% of total calls',
            icon: <TransferIcon />,
            miniChartData: [50, 45, 40, 55, 35, 30, 25],
        },
    ];

    // Sample data for the bar chart
    const chartData = [
        { day: 'Mon', automated: 280, transferred: 95 },
        { day: 'Tue', automated: 310, transferred: 88 },
        { day: 'Wed', automated: 295, transferred: 102 },
        { day: 'Thu', automated: 340, transferred: 78 },
        { day: 'Fri', automated: 385, transferred: 110 },
        { day: 'Sat', automated: 250, transferred: 125 },
        { day: 'Sun', automated: 274, transferred: 115 },
    ];

    const maxValue = Math.max(...chartData.flatMap(d => [d.automated, d.transferred]));

    const additionalStats = [
        {
            icon: <ClockIcon />,
            label: 'Avg. Call Duration',
            value: '2:34',
            change: '+12s',
            positive: true,
        },
        {
            icon: <StarIcon />,
            label: 'Customer Satisfaction',
            value: '4.8/5',
            change: '+0.3',
            positive: true,
        },
        {
            icon: <ZapIcon />,
            label: 'Response Time',
            value: '1.2s',
            change: '-0.4s',
            positive: true,
        },
        {
            icon: <CheckCircleIcon />,
            label: 'Resolution Rate',
            value: '94.2%',
            change: '+2.1%',
            positive: true,
        },
    ];

    return (
        <div className="analytics">
            {/* Header Section */}
            <div className="analytics-header">
                <div className="analytics-header-content">
                    <h1 className="analytics-title">Analytics</h1>
                    <p className="analytics-subtitle">Track your voice assistant's performance and call metrics.</p>
                    <div className="date-range-selector">
                        {dateRanges.map((range) => (
                            <button
                                key={range.id}
                                className={`date-btn ${selectedRange === range.id ? 'active' : ''}`}
                                onClick={() => setSelectedRange(range.id)}
                            >
                                {range.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Metric Cards */}
            <div className="metrics-grid">
                {metrics.map((metric) => (
                    <div key={metric.id} className={`metric-card ${metric.id}`}>
                        <div className="metric-header">
                            <div className={`metric-icon ${metric.id}`}>
                                {metric.icon}
                            </div>
                            <div className={`metric-trend ${metric.trendDirection === 'up' ? 'up' : metric.trendDirection === 'down' ? 'down' : 'neutral'}`}>
                                {metric.trendDirection === 'up' ? <TrendUpIcon /> : <TrendDownIcon />}
                                {metric.trend}
                            </div>
                        </div>
                        <div className="metric-content">
                            <span className="metric-value">{metric.value}</span>
                            <span className="metric-label">{metric.label}</span>
                            <span className="metric-description">{metric.description}</span>
                        </div>
                        <div className="metric-mini-chart">
                            {metric.miniChartData.map((height, index) => (
                                <div
                                    key={index}
                                    className={`mini-bar ${metric.id}`}
                                    style={{ height: `${height}%` }}
                                />
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts Section */}
            <div className="charts-grid">
                {/* Bar Chart */}
                <div className="chart-card">
                    <div className="chart-header">
                        <h2 className="chart-title">Call Volume Breakdown</h2>
                        <div className="chart-legend">
                            <div className="legend-item">
                                <span className="legend-dot automated"></span>
                                Automated
                            </div>
                            <div className="legend-item">
                                <span className="legend-dot transferred"></span>
                                Transferred
                            </div>
                        </div>
                    </div>
                    <div className="chart-placeholder">
                        <div className="chart-y-axis">
                            <span className="y-label">400</span>
                            <span className="y-label">300</span>
                            <span className="y-label">200</span>
                            <span className="y-label">100</span>
                            <span className="y-label">0</span>
                        </div>
                        <div className="chart-area">
                            <div className="chart-grid">
                                <div className="grid-line" style={{ top: '0%' }}></div>
                                <div className="grid-line" style={{ top: '25%' }}></div>
                                <div className="grid-line" style={{ top: '50%' }}></div>
                                <div className="grid-line" style={{ top: '75%' }}></div>
                                <div className="grid-line" style={{ top: '100%' }}></div>
                                <div className="chart-bars">
                                    {chartData.map((data, index) => (
                                        <div key={index} className="bar-group">
                                            <div
                                                className="bar automated"
                                                style={{ height: `${(data.automated / maxValue) * 100}%` }}
                                                title={`Automated: ${data.automated}`}
                                            />
                                            <div
                                                className="bar transferred"
                                                style={{ height: `${(data.transferred / maxValue) * 100}%` }}
                                                title={`Transferred: ${data.transferred}`}
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <div className="chart-x-axis">
                            {chartData.map((data, index) => (
                                <span key={index} className="x-label">{data.day}</span>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Donut Chart */}
                <div className="chart-card">
                    <div className="chart-header">
                        <h2 className="chart-title">Call Distribution</h2>
                    </div>
                    <div className="donut-chart-container">
                        <div className="donut-chart">
                            <div className="donut-center">
                                <span className="donut-value">2,847</span>
                                <span className="donut-label">Total Calls</span>
                            </div>
                        </div>
                        <div className="donut-legend">
                            <div className="donut-legend-item">
                                <div className="donut-legend-left">
                                    <span className="donut-legend-dot automated"></span>
                                    <span className="donut-legend-text">Automated</span>
                                </div>
                                <span className="donut-legend-value">74.9%</span>
                            </div>
                            <div className="donut-legend-item">
                                <div className="donut-legend-left">
                                    <span className="donut-legend-dot transferred"></span>
                                    <span className="donut-legend-text">Transferred</span>
                                </div>
                                <span className="donut-legend-value">25.1%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Additional Stats */}
            <div className="additional-stats">
                {additionalStats.map((stat, index) => (
                    <div key={index} className="stat-item">
                        <div className="stat-item-header">
                            <div className="stat-item-icon">
                                {stat.icon}
                            </div>
                            <span className="stat-item-label">{stat.label}</span>
                        </div>
                        <div className="stat-item-value">{stat.value}</div>
                        <div className="stat-item-change">
                            <span className={stat.positive ? 'positive' : 'negative'}>
                                {stat.change}
                            </span> vs last period
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Analytics;
