import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import {
  FiSearch,
  FiFilter,
  FiChevronDown,
  FiChevronUp,
  FiEdit2,
  FiTrash2,
  FiPhone,
  FiMail,
  FiBriefcase,
  FiUsers,
  FiMonitor,
  FiAlertCircle,
  FiSmile,
  FiMeh,
  FiFrown,
  FiCalendar,
  FiClock,
  FiChevronLeft,
  FiChevronRight,
} from 'react-icons/fi';
import {
  fetchInteractions,
  deleteInteraction,
  setFilters,
  setCurrentInteraction,
} from '../store/slices/interactionSlice';
import { format, parseISO } from 'date-fns';
import EditInteractionModal from './EditInteractionModal';

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

const typeIcons = {
  call: FiPhone,
  email: FiMail,
  visit: FiBriefcase,
  conference: FiUsers,
  virtual: FiMonitor,
};

function InteractionList() {
  const dispatch = useDispatch();
  const { interactions, loading, error, filters } = useSelector(
    (state) => state.interactions
  );
  const [expandedId, setExpandedId] = useState(null);
  const [editModal, setEditModal] = useState(null);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    dispatch(fetchInteractions({}));
  }, [dispatch]);

  const handleFilterChange = (field, value) => {
    dispatch(setFilters({ [field]: value }));
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this interaction?')) return;
    try {
      await dispatch(deleteInteraction(id)).unwrap();
      toast.success('Interaction deleted');
    } catch (err) {
      toast.error(err || 'Failed to delete');
    }
  };

  const handleEdit = (interaction, e) => {
    e.stopPropagation();
    setEditModal(interaction);
  };

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const formatDate = (dateStr) => {
    try {
      return format(parseISO(dateStr), 'MMM d, yyyy');
    } catch {
      return dateStr || 'N/A';
    }
  };

  // Apply client-side filters
  const filtered = interactions.filter((i) => {
    if (
      filters.search &&
      !(i.hcp_name || i.hcp?.name || i.raw_notes || '')
        .toLowerCase()
        .includes(filters.search.toLowerCase())
    ) {
      return false;
    }
    if (
      filters.interactionType &&
      i.interaction_type !== filters.interactionType
    ) {
      return false;
    }
    if (filters.sentiment && i.sentiment !== filters.sentiment) {
      return false;
    }
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  const SentimentIcon = ({ sentiment }) => {
    switch (sentiment) {
      case 'positive':
        return <FiSmile size={14} />;
      case 'negative':
        return <FiFrown size={14} />;
      default:
        return <FiMeh size={14} />;
    }
  };

  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <div className="page-header">
        <h2>Interactions</h2>
        <p>Browse and manage all HCP interaction records</p>
      </div>

      {/* Filter Bar */}
      <div className="filter-bar">
        <div className="search-input" style={{ position: 'relative', flex: 1 }}>
          <FiSearch
            style={{
              position: 'absolute',
              left: '14px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
              pointerEvents: 'none',
            }}
          />
          <input
            type="text"
            className="form-input"
            placeholder="Search by HCP name or notes..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            style={{ paddingLeft: '40px', width: '100%' }}
          />
        </div>
        <select
          className="form-select"
          value={filters.interactionType}
          onChange={(e) => handleFilterChange('interactionType', e.target.value)}
        >
          <option value="">All Types</option>
          <option value="call">Call</option>
          <option value="email">Email</option>
          <option value="visit">Visit</option>
          <option value="conference">Conference</option>
          <option value="virtual">Virtual</option>
        </select>
        <select
          className="form-select"
          value={filters.sentiment}
          onChange={(e) => handleFilterChange('sentiment', e.target.value)}
        >
          <option value="">All Sentiments</option>
          <option value="positive">Positive</option>
          <option value="neutral">Neutral</option>
          <option value="negative">Negative</option>
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="error-state" style={{ marginBottom: '24px' }}>
          <FiAlertCircle className="error-state-icon" />
          <div className="error-state-message">{error}</div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => dispatch(fetchInteractions({}))}
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && interactions.length === 0 ? (
        <div className="loading-container">
          <div className="spinner" />
          <div className="loading-text">Loading interactions...</div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <FiFilter />
          </div>
          <div className="empty-state-title">No interactions found</div>
          <div className="empty-state-description">
            {filters.search || filters.interactionType || filters.sentiment
              ? 'Try adjusting your filters'
              : 'Start by logging your first interaction'}
          </div>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="glass-card-static" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="interaction-table">
              <thead>
                <tr>
                  <th>HCP</th>
                  <th>Type</th>
                  <th>Date</th>
                  <th>Sentiment</th>
                  <th>Duration</th>
                  <th>Actions</th>
                  <th style={{ width: '40px' }} />
                </tr>
              </thead>
              <tbody>
                {paginated.map((interaction) => {
                  const TypeIcon = typeIcons[interaction.interaction_type] || FiPhone;
                  const isExpanded = expandedId === interaction.id;
                  const hcpName =
                    interaction.hcp_name ||
                    interaction.hcp?.name ||
                    `HCP #${interaction.hcp_id || '?'}`;

                  return (
                    <React.Fragment key={interaction.id}>
                      <tr onClick={() => toggleExpand(interaction.id)}>
                        <td>
                          <div style={{ fontWeight: 500 }}>{hcpName}</div>
                        </td>
                        <td>
                          <span
                            className={`type-badge ${interaction.interaction_type || 'call'}`}
                          >
                            <TypeIcon size={12} />
                            {interaction.interaction_type || 'call'}
                          </span>
                        </td>
                        <td>
                          <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                            {formatDate(
                              interaction.interaction_date ||
                                interaction.date ||
                                interaction.created_at
                            )}
                          </span>
                        </td>
                        <td>
                          {interaction.sentiment ? (
                            <span
                              className={`sentiment-badge ${interaction.sentiment}`}
                            >
                              <SentimentIcon sentiment={interaction.sentiment} />
                              {interaction.sentiment}
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>—</span>
                          )}
                        </td>
                        <td>
                          <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                            {interaction.duration_minutes
                              ? `${interaction.duration_minutes} min`
                              : '—'}
                          </span>
                        </td>
                        <td>
                          <div className="table-actions">
                            <button
                              className="btn btn-ghost edit"
                              onClick={(e) => handleEdit(interaction, e)}
                              title="Edit"
                            >
                              <FiEdit2 size={15} />
                            </button>
                            <button
                              className="btn btn-ghost delete"
                              onClick={(e) => handleDelete(interaction.id, e)}
                              title="Delete"
                            >
                              <FiTrash2 size={15} />
                            </button>
                          </div>
                        </td>
                        <td>
                          {isExpanded ? (
                            <FiChevronUp size={16} color="var(--text-muted)" />
                          ) : (
                            <FiChevronDown size={16} color="var(--text-muted)" />
                          )}
                        </td>
                      </tr>

                      {/* Expanded Detail */}
                      {isExpanded && (
                        <tr className="interaction-expanded">
                          <td colSpan={7}>
                            <div className="interaction-detail-grid">
                              <div className="interaction-detail-item">
                                <span className="interaction-detail-label">
                                  Raw Notes
                                </span>
                                <span className="interaction-detail-value">
                                  {interaction.raw_notes || 'No notes recorded'}
                                </span>
                              </div>
                              <div className="interaction-detail-item">
                                <span className="interaction-detail-label">
                                  AI Summary
                                </span>
                                <span className="interaction-detail-value">
                                  {interaction.ai_summary || 'No AI summary available'}
                                </span>
                              </div>
                              <div className="interaction-detail-item">
                                <span className="interaction-detail-label">
                                  Products Discussed
                                </span>
                                <span className="interaction-detail-value">
                                  {interaction.products_discussed &&
                                  interaction.products_discussed.length > 0
                                    ? interaction.products_discussed.join(', ')
                                    : 'None'}
                                </span>
                              </div>
                              <div className="interaction-detail-item">
                                <span className="interaction-detail-label">
                                  Follow-up
                                </span>
                                <span className="interaction-detail-value">
                                  {interaction.follow_up_required
                                    ? `Yes${
                                        interaction.follow_up_date
                                          ? ` — ${formatDate(interaction.follow_up_date)}`
                                          : ''
                                      }`
                                    : 'Not required'}
                                </span>
                              </div>
                              {interaction.key_topics &&
                                interaction.key_topics.length > 0 && (
                                  <div className="interaction-detail-item">
                                    <span className="interaction-detail-label">
                                      Key Topics
                                    </span>
                                    <div className="chips-container" style={{ marginTop: '4px' }}>
                                      {interaction.key_topics.map((topic, i) => (
                                        <span key={i} className="chip">
                                          {topic}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="pagination-btn"
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <FiChevronLeft size={16} />
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  className={`pagination-btn ${p === page ? 'active' : ''}`}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              ))}
              <button
                className="pagination-btn"
                disabled={page === totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                <FiChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}

      {/* Edit Modal */}
      <AnimatePresence>
        {editModal && (
          <EditInteractionModal
            interaction={editModal}
            onClose={() => setEditModal(null)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default InteractionList;
