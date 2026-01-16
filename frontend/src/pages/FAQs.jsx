import React, { useState } from 'react';
import './FAQs.css';

// SVG Icons
const FAQIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
);

const PlusIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
);

const EditIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
);

const DeleteIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="3 6 5 6 21 6" />
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        <line x1="10" y1="11" x2="10" y2="17" />
        <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
);

const CloseIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
);

const SearchIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
);

const FAQs = () => {
    // Initial FAQ data
    const initialFAQs = [
        {
            id: 1,
            question: 'What are your business hours?',
            answer: 'Our business hours are Monday to Friday, 9 AM to 6 PM EST. We are closed on weekends and major holidays.',
            category: 'General'
        },
        {
            id: 2,
            question: 'How can I track my order?',
            answer: 'You can track your order by logging into your account and visiting the "Order History" section. You will also receive email updates with tracking information.',
            category: 'Orders'
        },
        {
            id: 3,
            question: 'What is your refund policy?',
            answer: 'We offer a 30-day money-back guarantee. If you are not satisfied with your purchase, please contact our support team for a full refund.',
            category: 'Billing'
        },
        {
            id: 4,
            question: 'How do I reset my password?',
            answer: 'Click on "Forgot Password" on the login page. Enter your email address and we will send you a password reset link.',
            category: 'Account'
        },
        {
            id: 5,
            question: 'Do you offer technical support?',
            answer: 'Yes, we offer 24/7 technical support via phone, email, and live chat. Our team is always ready to help you with any issues.',
            category: 'Support'
        },
    ];

    const [faqs, setFAQs] = useState(initialFAQs);
    const [searchQuery, setSearchQuery] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingFAQ, setEditingFAQ] = useState(null);
    const [formData, setFormData] = useState({ question: '', answer: '', category: 'General' });
    const [deleteConfirm, setDeleteConfirm] = useState(null);

    const categories = ['General', 'Orders', 'Billing', 'Account', 'Support', 'Technical'];

    // Filter FAQs based on search
    const filteredFAQs = faqs.filter(faq =>
        faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Open modal for adding new FAQ
    const handleAddNew = () => {
        setEditingFAQ(null);
        setFormData({ question: '', answer: '', category: 'General' });
        setIsModalOpen(true);
    };

    // Open modal for editing FAQ
    const handleEdit = (faq) => {
        setEditingFAQ(faq);
        setFormData({ question: faq.question, answer: faq.answer, category: faq.category });
        setIsModalOpen(true);
    };

    // Close modal
    const handleCloseModal = () => {
        setIsModalOpen(false);
        setEditingFAQ(null);
        setFormData({ question: '', answer: '', category: 'General' });
    };

    // Handle form input change
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    // Save FAQ (add or edit)
    const handleSave = () => {
        if (!formData.question.trim() || !formData.answer.trim()) return;

        if (editingFAQ) {
            // Update existing FAQ
            setFAQs(prev => prev.map(faq =>
                faq.id === editingFAQ.id
                    ? { ...faq, ...formData }
                    : faq
            ));
        } else {
            // Add new FAQ
            const newFAQ = {
                id: Date.now(),
                ...formData
            };
            setFAQs(prev => [newFAQ, ...prev]);
        }
        handleCloseModal();
    };

    // Delete FAQ
    const handleDelete = (id) => {
        setFAQs(prev => prev.filter(faq => faq.id !== id));
        setDeleteConfirm(null);
    };

    return (
        <div className="faqs-page">
            {/* Header Section */}
            <div className="page-header">
                <div className="page-header-content">
                    <div className="page-header-icon">
                        <FAQIcon />
                    </div>
                    <div>
                        <h1 className="page-title">FAQs / Responses</h1>
                        <p className="page-subtitle">Manage automated responses for common questions</p>
                    </div>
                </div>
            </div>

            {/* Actions Bar */}
            <div className="actions-bar">
                <div className="search-wrapper">
                    <span className="search-icon"><SearchIcon /></span>
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Search FAQs..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <button className="add-button" onClick={handleAddNew}>
                    <PlusIcon />
                    <span>Add New FAQ</span>
                </button>
            </div>

            {/* Stats Bar */}
            <div className="stats-bar">
                <span className="stats-text">
                    {filteredFAQs.length} FAQ{filteredFAQs.length !== 1 ? 's' : ''} found
                </span>
            </div>

            {/* FAQ List */}
            <div className="faq-list">
                {filteredFAQs.length > 0 ? (
                    filteredFAQs.map((faq, index) => (
                        <div key={faq.id} className="faq-card" style={{ animationDelay: `${index * 0.05}s` }}>
                            <div className="faq-content">
                                <div className="faq-header">
                                    <span className={`faq-category category-${faq.category.toLowerCase()}`}>
                                        {faq.category}
                                    </span>
                                    <div className="faq-actions">
                                        <button
                                            className="action-btn edit-btn"
                                            onClick={() => handleEdit(faq)}
                                            title="Edit FAQ"
                                        >
                                            <EditIcon />
                                        </button>
                                        <button
                                            className="action-btn delete-btn"
                                            onClick={() => setDeleteConfirm(faq.id)}
                                            title="Delete FAQ"
                                        >
                                            <DeleteIcon />
                                        </button>
                                    </div>
                                </div>
                                <h3 className="faq-question">{faq.question}</h3>
                                <p className="faq-answer">{faq.answer}</p>
                            </div>

                            {/* Delete Confirmation */}
                            {deleteConfirm === faq.id && (
                                <div className="delete-confirm">
                                    <p>Are you sure you want to delete this FAQ?</p>
                                    <div className="delete-confirm-actions">
                                        <button
                                            className="confirm-btn cancel"
                                            onClick={() => setDeleteConfirm(null)}
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            className="confirm-btn delete"
                                            onClick={() => handleDelete(faq.id)}
                                        >
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                ) : (
                    <div className="empty-state">
                        <FAQIcon />
                        <h3>No FAQs Found</h3>
                        <p>
                            {searchQuery
                                ? 'No FAQs match your search criteria'
                                : 'Get started by adding your first FAQ'}
                        </p>
                        {!searchQuery && (
                            <button className="add-button" onClick={handleAddNew}>
                                <PlusIcon />
                                <span>Add Your First FAQ</span>
                            </button>
                        )}
                    </div>
                )}
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div className="modal-overlay" onClick={handleCloseModal}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{editingFAQ ? 'Edit FAQ' : 'Add New FAQ'}</h2>
                            <button className="modal-close" onClick={handleCloseModal}>
                                <CloseIcon />
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label className="form-label">Category</label>
                                <select
                                    name="category"
                                    className="form-select"
                                    value={formData.category}
                                    onChange={handleInputChange}
                                >
                                    {categories.map(cat => (
                                        <option key={cat} value={cat}>{cat}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Question</label>
                                <input
                                    type="text"
                                    name="question"
                                    className="form-input"
                                    placeholder="Enter the frequently asked question..."
                                    value={formData.question}
                                    onChange={handleInputChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Answer</label>
                                <textarea
                                    name="answer"
                                    className="form-textarea"
                                    placeholder="Enter the response for this question..."
                                    rows="5"
                                    value={formData.answer}
                                    onChange={handleInputChange}
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="modal-btn cancel" onClick={handleCloseModal}>
                                Cancel
                            </button>
                            <button
                                className="modal-btn save"
                                onClick={handleSave}
                                disabled={!formData.question.trim() || !formData.answer.trim()}
                            >
                                {editingFAQ ? 'Save Changes' : 'Add FAQ'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FAQs;
