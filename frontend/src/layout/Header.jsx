import React from 'react';
import { useUser, UserButton, SignInButton, SignUpButton } from '@clerk/clerk-react';
import './Header.css';

const Header = ({ title }) => {
    const { isSignedIn, user } = useUser();

    return (
        <header className="header">
            <div className="header-content">
                <h1 className="header-title">{title || 'Dashboard'}</h1>
            </div>
            <div className="header-actions">
                <div className="header-user">
                    {isSignedIn ? (
                        <div className="user-info">
                            <span className="user-name">{user?.firstName || 'Admin'}</span>
                            <UserButton afterSignOutUrl="/sign-in" />
                        </div>
                    ) : (
                        <div className="auth-buttons">
                            <SignInButton mode="modal">
                                <button className="sign-in-btn">Sign In</button>
                            </SignInButton>
                            <SignUpButton mode="modal">
                                <button className="sign-up-btn">Sign Up</button>
                            </SignUpButton>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
};

export default Header;
