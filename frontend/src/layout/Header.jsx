import React from 'react';
import './Header.css';

const Header = ({ title }) => {
    return (
        <header className="header">
            <div className="header-content">
                <h1 className="header-title">{title || 'Dashboard'}</h1>
            </div>
            <div className="header-actions">
                <div className="header-user">
                    <span className="user-avatar">👤</span>
                    <span className="user-name">Admin</span>
                </div>
            </div>
        </header>
    );
};

export default Header;
