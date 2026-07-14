import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useNavigate } from "react-router-dom";
import {
  FiEdit3,
  FiMessageCircle,
  FiPhone,
  FiMail,
  FiBriefcase,
  FiMonitor,
  FiUsers,
  FiCalendar,
  FiClock,
  FiSend,
  FiZap,
  FiSmile,
  FiMeh,
  FiFrown,
  FiPlus,
  FiX,
  FiCheck,
  FiLoader,
  FiCpu,
  FiTool,
  FiSearch,
  FiUser,
  FiTarget,
  FiMapPin,
} from 'react-icons/fi';
import { fetchHCPs } from '../store/slices/hcpSlice';
import {
  createInteraction,
  processNotes,
  clearProcessedNotes,
} from '../store/slices/interactionSlice';
import {
  sendMessage,
  addMessage,
  clearMessages,
  setTyping,
} from '../store/slices/chatSlice';
import { format } from 'date-fns';

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

const INTERACTION_TYPES = [
  { value: 'call', label: 'Call', icon: FiPhone },
  { value: 'email', label: 'Email', icon: FiMail },
  { value: 'visit', label: 'Visit', icon: FiBriefcase },
  { value: 'conference', label: 'Conference', icon: FiUsers },
  { value: 'virtual', label: 'Virtual', icon: FiMonitor },
];

const QUICK_ACTIONS = [
  'Log a new interaction',
  'Search interactions',
  'HCP profile lookup',
  'Suggest next action',
];

function LogInteraction() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { hcps } = useSelector((state) => state.hcps);
  const { loading, processedNotes, processingNotes } = useSelector(
    (state) => state.interactions
  );
  const { messages, isTyping } = useSelector((state) => state.chat);

  const [activeTab, setActiveTab] = useState('form');
  const [hcpSearch, setHcpSearch] = useState('');
  const [showHcpDropdown, setShowHcpDropdown] = useState(false);

  // Form state
  const [form, setForm] = useState({
    hcp_id: '',
    hcp_name: '',
    interaction_type: 'call',
    interaction_date: format(new Date(), 'yyyy-MM-dd'),
    duration_minutes: 30,
    raw_notes: '',
    products_discussed: [],
    sentiment: '',
    follow_up_required: false,
    follow_up_date: '',
    follow_up_notes: '',
    ai_summary: '',
    key_topics: [],
  });

  const [productInput, setProductInput] = useState('');

  // Chat state
  const [chatInput, setChatInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const chatMessagesRef = useRef(null);
  const chatInputRef = useRef(null);
  const hcpDropdownRef = useRef(null);

  useEffect(() => {
    dispatch(fetchHCPs({}));
    return () => {
      dispatch(clearProcessedNotes());
    };
  }, [dispatch]);

  // Auto-scroll chat
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // Close HCP dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (hcpDropdownRef.current && !hcpDropdownRef.current.contains(e.target)) {
        setShowHcpDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Apply AI processed notes to form
  useEffect(() => {
    if (processedNotes) {
      setForm((prev) => ({
        ...prev,
        ai_summary: processedNotes.summary || processedNotes.ai_summary || '',
        key_topics: processedNotes.key_topics || processedNotes.topics || [],
        sentiment: processedNotes.sentiment || prev.sentiment,
        products_discussed:
          processedNotes.products_discussed ||
          processedNotes.products ||
          prev.products_discussed,
      }));
      toast.success('AI processing complete!');
    }
  }, [processedNotes]);

  const filteredHcps = hcps.filter((hcp) => {
    const name = (hcp.name || hcp.full_name || '').toLowerCase();
    return name.includes(hcpSearch.toLowerCase());
  });

  const selectHcp = (hcp) => {
    setForm((prev) => ({
      ...prev,
      hcp_id: hcp.id,
      hcp_name: hcp.name || hcp.full_name || '',
    }));
    setHcpSearch(hcp.name || hcp.full_name || '');
    setShowHcpDropdown(false);
  };

  const handleFormChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const addProduct = () => {
    const trimmed = productInput.trim();
    if (trimmed && !form.products_discussed.includes(trimmed)) {
      setForm((prev) => ({
        ...prev,
        products_discussed: [...prev.products_discussed, trimmed],
      }));
      setProductInput('');
    }
  };

  const removeProduct = (product) => {
    setForm((prev) => ({
      ...prev,
      products_discussed: prev.products_discussed.filter((p) => p !== product),
    }));
  };

  const handleProductKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addProduct();
    }
  };

  const handleProcessNotes = () => {
    if (!form.raw_notes.trim()) {
      toast.error('Please enter some notes to process');
      return;
    }
    dispatch(processNotes(form.raw_notes));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.hcp_id) {
      toast.error('Please select an HCP');
      return;
    }
    if (!form.interaction_type) {
      toast.error('Please select an interaction type');
      return;
    }

    const payload = {
      hcp_id: form.hcp_id,
      interaction_type: form.interaction_type,
      interaction_date: form.interaction_date,
      duration_minutes: parseInt(form.duration_minutes) || 0,
      raw_notes: form.raw_notes,
      ai_summary: form.ai_summary,
      products_discussed: form.products_discussed,
      sentiment: form.sentiment || undefined,
      key_topics: form.key_topics,
      follow_up_required: form.follow_up_required,
      follow_up_date: form.follow_up_required ? form.follow_up_date || undefined : undefined,
      follow_up_notes: form.follow_up_required ? form.follow_up_notes || undefined : undefined,
    };

    try {
      await dispatch(createInteraction(payload)).unwrap();
      toast.success('Interaction logged successfully!');
      // Reset form
      setForm({
        hcp_id: '',
        hcp_name: '',
        interaction_type: 'call',
        interaction_date: format(new Date(), 'yyyy-MM-dd'),
        duration_minutes: 30,
        raw_notes: '',
        products_discussed: [],
        sentiment: '',
        follow_up_required: false,
        follow_up_date: '',
        follow_up_notes: '',
        ai_summary: '',
        key_topics: [],
      });
      setHcpSearch('');
      dispatch(clearProcessedNotes());
    } catch (err) {
      toast.error(err || 'Failed to log interaction');
    }
  };

  // ─── Chat handlers ───────────────────────────────────────────────────────
  const handleSendChat = useCallback(async () => {
    const trimmed = chatInput.trim();
    if (!trimmed || isTyping) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString(),
    };

    dispatch(addMessage(userMessage));
    setChatInput('');

    try {
      await dispatch(sendMessage(trimmed)).unwrap();
    } catch {
      // Error handled in the slice
    }
  }, [chatInput, isTyping, dispatch]);

  const handleChatKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendChat();
    }
  };

  const handleQuickAction = (action) => {
    setChatInput(action);
    if (chatInputRef.current) {
      chatInputRef.current.focus();
    }
  };

  const handleClearChat = () => {
    dispatch(clearMessages());
  };

  const formatTime = (timestamp) => {
    try {
      return format(new Date(timestamp), 'HH:mm');
    } catch {
      return '';
    }
  };

  // Tab indicator positioning
  const tabIndicatorStyle =
    activeTab === 'form'
      ? { left: '4px', width: 'calc(50% - 4px)' }
      : { left: 'calc(50%)', width: 'calc(50% - 4px)' };

  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <div className="page-header">
        <h2>Log Interaction</h2>
        <p>Record HCP engagement using the structured form or chat with the AI agent</p>
      </div>

      {/* Tab Toggle */}
      <div className="tab-toggle">
        <motion.div
          className="tab-toggle-indicator"
          animate={tabIndicatorStyle}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        />
        <button
          className={`tab-toggle-btn ${activeTab === 'form' ? 'active' : ''}`}
          onClick={() => setActiveTab('form')}
        >
          <FiEdit3 size={16} /> Structured Form
        </button>
        <button
          className={`tab-toggle-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <FiMessageCircle size={16} /> AI Chat
        </button>
      </div>

      <AnimatePresence mode="wait">
        {activeTab === 'form' ? (
          <motion.div
            key="form"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
          >
            {/* ─── STRUCTURED FORM ─────────────────────────────────────────── */}
            <form onSubmit={handleSubmit} className="log-interaction-layout">
              <div className="glass-card-static">
                {/* HCP Select */}
                <div className="form-group" ref={hcpDropdownRef}>
                  <label className="form-label">Healthcare Professional</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Search and select an HCP..."
                      value={hcpSearch}
                      onChange={(e) => {
                        setHcpSearch(e.target.value);
                        setShowHcpDropdown(true);
                        if (!e.target.value) {
                          handleFormChange('hcp_id', '');
                          handleFormChange('hcp_name', '');
                        }
                      }}
                      onFocus={() => setShowHcpDropdown(true)}
                    />
                    {showHcpDropdown && filteredHcps.length > 0 && (
                      <div
                        style={{
                          position: 'absolute',
                          top: '100%',
                          left: 0,
                          right: 0,
                          background: 'var(--bg-surface)',
                          border: '1px solid var(--border-color)',
                          borderRadius: 'var(--radius-sm)',
                          marginTop: '4px',
                          maxHeight: '200px',
                          overflowY: 'auto',
                          zIndex: 50,
                          boxShadow: 'var(--shadow-lg)',
                        }}
                      >
                        {filteredHcps.map((hcp) => (
                          <div
                            key={hcp.id}
                            onClick={() => selectHcp(hcp)}
                            style={{
                              padding: '10px 16px',
                              cursor: 'pointer',
                              fontSize: '14px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '10px',
                              transition: 'var(--transition-fast)',
                              borderBottom: '1px solid var(--border-color)',
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = 'var(--bg-card-hover)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = 'transparent';
                            }}
                          >
                            <FiUser style={{ color: 'var(--primary)', flexShrink: 0 }} />
                            <div>
                              <div style={{ fontWeight: 500 }}>
                                {hcp.name || hcp.full_name}
                              </div>
                              <div
                                style={{
                                  fontSize: '12px',
                                  color: 'var(--text-muted)',
                                }}
                              >
                                {hcp.specialty || ''}{' '}
                                {hcp.institution ? `· ${hcp.institution}` : ''}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Interaction Type */}
                <div className="form-group">
                  <label className="form-label">Interaction Type</label>
                  <div className="type-cards">
                    {INTERACTION_TYPES.map((type) => (
                      <div
                        key={type.value}
                        className={`type-card ${
                          form.interaction_type === type.value ? 'selected' : ''
                        }`}
                        onClick={() => handleFormChange('interaction_type', type.value)}
                      >
                        <type.icon className="type-card-icon" />
                        {type.label}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Date & Duration */}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">
                      <FiCalendar size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                      Date
                    </label>
                    <input
                      type="date"
                      className="form-input"
                      value={form.interaction_date}
                      onChange={(e) =>
                        handleFormChange('interaction_date', e.target.value)
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">
                      <FiClock size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                      Duration (minutes)
                    </label>
                    <input
                      type="number"
                      className="form-input"
                      min="1"
                      max="480"
                      value={form.duration_minutes}
                      onChange={(e) =>
                        handleFormChange('duration_minutes', e.target.value)
                      }
                    />
                  </div>
                </div>

                {/* Raw Notes */}
                <div className="form-group">
                  <label className="form-label">Notes</label>
                  <textarea
                    className="form-textarea"
                    placeholder="Enter your interaction notes here... The AI can summarize and extract key information."
                    rows={5}
                    value={form.raw_notes}
                    onChange={(e) => handleFormChange('raw_notes', e.target.value)}
                  />
                  <div style={{ marginTop: '12px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={handleProcessNotes}
                      disabled={processingNotes || !form.raw_notes.trim()}
                    >
                      {processingNotes ? (
                        <>
                          <span className="spinner spinner-inline" /> Processing...
                        </>
                      ) : (
                        <>
                          <FiZap /> Process with AI
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* AI Processing Animation */}
                {processingNotes && (
                  <div className="processing-animation">
                    <div className="spinner spinner-sm" />
                    <span className="processing-text">
                      AI is analyzing your notes, extracting key topics and sentiment...
                    </span>
                  </div>
                )}

                {/* AI Summary Display */}
                {form.ai_summary && (
                  <motion.div
                    className="ai-summary-card"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="ai-summary-header">
                      <FiCpu size={16} /> AI Summary
                    </div>
                    <div className="ai-summary-content">
                      <p>{form.ai_summary}</p>
                      {form.key_topics && form.key_topics.length > 0 && (
                        <>
                          <h4>Key Topics</h4>
                          <div className="ai-summary-topics">
                            {form.key_topics.map((topic, i) => (
                              <span key={i} className="ai-summary-topic-tag">
                                {topic}
                              </span>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </motion.div>
                )}

                {/* Products Discussed */}
                <div className="form-group" style={{ marginTop: '20px' }}>
                  <label className="form-label">Products Discussed</label>
                  <div className="product-input-row">
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Type product name and press Enter"
                      value={productInput}
                      onChange={(e) => setProductInput(e.target.value)}
                      onKeyDown={handleProductKeyDown}
                    />
                    <button
                      type="button"
                      className="btn btn-secondary btn-icon"
                      onClick={addProduct}
                    >
                      <FiPlus />
                    </button>
                  </div>
                  {form.products_discussed.length > 0 && (
                    <div className="chips-container">
                      {form.products_discussed.map((product) => (
                        <span key={product} className="chip selected">
                          {product}
                          <span
                            className="chip-remove"
                            onClick={() => removeProduct(product)}
                          >
                            <FiX size={14} />
                          </span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Sentiment */}
                <div className="form-group">
                  <label className="form-label">Sentiment</label>
                  <div className="sentiment-selector">
                    <div
                      className={`sentiment-option positive ${
                        form.sentiment === 'positive' ? 'selected' : ''
                      }`}
                      onClick={() => handleFormChange('sentiment', 'positive')}
                    >
                      <FiSmile /> Positive
                    </div>
                    <div
                      className={`sentiment-option neutral ${
                        form.sentiment === 'neutral' ? 'selected' : ''
                      }`}
                      onClick={() => handleFormChange('sentiment', 'neutral')}
                    >
                      <FiMeh /> Neutral
                    </div>
                    <div
                      className={`sentiment-option negative ${
                        form.sentiment === 'negative' ? 'selected' : ''
                      }`}
                      onClick={() => handleFormChange('sentiment', 'negative')}
                    >
                      <FiFrown /> Negative
                    </div>
                  </div>
                </div>

                {/* Follow-up */}
                <div className="form-group">
                  <label className="form-label">Follow-up</label>
                  <div className="toggle-container">
                    <div
                      className={`toggle-switch ${
                        form.follow_up_required ? 'active' : ''
                      }`}
                      onClick={() =>
                        handleFormChange(
                          'follow_up_required',
                          !form.follow_up_required
                        )
                      }
                    >
                      <div className="toggle-switch-knob" />
                    </div>
                    <span className="toggle-label">Follow-up required</span>
                  </div>

                  <AnimatePresence>
                    {form.follow_up_required && (
                      <motion.div
                        className="followup-section"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className="form-row">
                          <div className="form-group" style={{ marginBottom: 0 }}>
                            <label className="form-label">Follow-up Date</label>
                            <input
                              type="date"
                              className="form-input"
                              value={form.follow_up_date}
                              onChange={(e) =>
                                handleFormChange('follow_up_date', e.target.value)
                              }
                            />
                          </div>
                          <div className="form-group" style={{ marginBottom: 0 }}>
                            <label className="form-label">Follow-up Notes</label>
                            <input
                              type="text"
                              className="form-input"
                              placeholder="Briefly describe follow-up action"
                              value={form.follow_up_notes}
                              onChange={(e) =>
                                handleFormChange('follow_up_notes', e.target.value)
                              }
                            />
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Submit */}
                <div style={{ marginTop: '24px' }}>
                  <button
                    type="submit"
                    className="btn btn-primary btn-lg"
                    disabled={loading}
                    style={{ width: '100%' }}
                  >
                    {loading ? (
                      <>
                        <span className="spinner spinner-inline" /> Saving...
                      </>
                    ) : (
                      <>
                        <FiCheck /> Log Interaction
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          </motion.div>
        ) : (
          <motion.div
            key="chat"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {/* ─── AI CHAT INTERFACE ──────────────────────────────────────── */}
            <div className="chat-container">
              {/* Header */}
              <div className="chat-header">
                <div className="chat-header-title">
                  <div className="chat-header-dot" />
                  <FiCpu size={18} />
                  PharmaPulse AI CRM Agent
                </div>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={handleClearChat}
                  disabled={messages.length === 0}
                >
                  Clear Chat
                </button>
              </div>

              {/* Messages */}
              <div className="chat-messages" ref={chatMessagesRef}>
                {messages.length === 0 && (
                  <div className="empty-state" style={{ padding: '40px 20px' }}>
                    <div className="empty-state-icon">
                      <FiMessageCircle />
                    </div>
                    <div className="empty-state-title">Start a conversation</div>
                    <div className="empty-state-description">
                      Ask me to log interactions, search HCP data, analyze sentiment,
                      or suggest next actions. I can help with anything CRM-related.
                    </div>
                  </div>
                )}

                {messages.map((msg) => (
                  <div key={msg.id} className={`chat-message ${msg.role}`}>
                    <div className="chat-message-avatar">
                      {msg.role === 'user' ? <FiUser size={14} /> : <FiCpu size={14} />}
                    </div>
                    <div>
                      <div
                          className={`chat-message-bubble ${
                            msg.isError ? "error" : ""
                          }`}
                        >
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>

                          {msg.role === "assistant" && !msg.isError && (
                            <div className="quick-action-buttons">

                              <button onClick={() => navigate("/hcps")}>
                                👤 View Profile
                              </button>

                              <button onClick={() => navigate("/interactions")}>
                                📜 View History
                              </button>

                              <button>
                                🧠 Next Best Action
                              </button>

                              <button>
                                ✏️ Edit Interaction
                              </button>

                              <button onClick={() => setChatInput("")}>
                                ➕ Log Another
                              </button>

                            </div>
                          )}
                        </div>

                      {/* Tool badges */}
                      {msg.tools && msg.tools.length > 0 && (
                        <div className="chat-tools-list">
                          {msg.tools.map((tool, i) => (
                            <span key={i} className="chat-tool-badge">
                              <FiTool size={10} /> {tool}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="chat-message-time">
                        {formatTime(msg.timestamp)}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Typing indicator */}
                {isTyping && (
                  <div className="typing-indicator">
                    <div className="typing-indicator-avatar">
                      <FiCpu size={14} />
                    </div>
                    <div>
                      <div className="typing-dots">
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                      </div>
                      <div className="chat-tool-indicator" style={{ marginTop: '8px' }}>
                        <FiLoader className="chat-tool-icon" size={14} />
                        Processing your request...
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="chat-input-area">
                {/* Quick actions */}
                {messages.length === 0 && (
                  <div className="chat-quick-actions">
                    {QUICK_ACTIONS.map((action) => (
                      <button
                        key={action}
                        className="chat-quick-action"
                        onClick={() => handleQuickAction(action)}
                      >
                        {action}
                      </button>
                    ))}
                  </div>
                )}

                <div className="chat-input-row">
                  <textarea
                    ref={chatInputRef}
                    className="chat-input"
                    placeholder="Ask the AI agent anything..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleChatKeyDown}
                    rows={1}
                    disabled={isTyping}
                  />
                  <button
                    className="chat-send-btn"
                    onClick={handleSendChat}
                    disabled={!chatInput.trim() || isTyping}
                  >
                    <FiSend />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default LogInteraction;
