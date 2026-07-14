import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiArrowLeft,
  FiUser,
  FiMapPin,
  FiBriefcase,
  FiMail,
  FiPhone,
  FiCalendar,
  FiMessageSquare,
  FiActivity,
  FiTarget,
  FiTrendingUp,
  FiClock,
  FiSmile,
  FiMeh,
  FiFrown,
} from 'react-icons/fi';
import { fetchHCPById, clearCurrentHcp } from '../store/slices/hcpSlice';
import { fetchInteractions } from '../store/slices/interactionSlice';
import { format, parseISO } from 'date-fns';

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

function HCPDetail() {
  const { id } = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { currentHcp, loading: hcpLoading } = useSelector((state) => state.hcps);
  const { interactions } = useSelector((state) => state.interactions);

  useEffect(() => {
    dispatch(fetchHCPById(id));
    dispatch(fetchInteractions({ hcp_id: id }));
    return () => {
      dispatch(clearCurrentHcp());
    };
  }, [dispatch, id]);

  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getTierClass = (tier) => {
    if (!tier) return 'tier-3';
    const t = String(tier).toLowerCase();
    if (t.includes('1') || t === 'platinum' || t === 'high') return 'tier-1';
    if (t.includes('2') || t === 'gold' || t === 'medium') return 'tier-2';
    return 'tier-3';
  };

  const formatDate = (dateStr) => {
    try {
      return format(parseISO(dateStr), 'MMM d, yyyy');
    } catch {
      return dateStr || 'N/A';
    }
  };

  // Compute product affinity from interactions
  const productCounts = {};
  const hcpInteractions = interactions.filter(
    (i) => String(i.hcp_id) === String(id)
  );

  hcpInteractions.forEach((interaction) => {
    (interaction.products_discussed || []).forEach((product) => {
      productCounts[product] = (productCounts[product] || 0) + 1;
    });
  });

  const productAffinities = Object.entries(productCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  const maxProductCount = productAffinities.length > 0
    ? Math.max(...productAffinities.map(([, count]) => count))
    : 1;

  // Compute metrics
  const sentimentCounts = { positive: 0, neutral: 0, negative: 0 };
  hcpInteractions.forEach((i) => {
    if (i.sentiment && sentimentCounts[i.sentiment] !== undefined) {
      sentimentCounts[i.sentiment]++;
    }
  });

  const totalDuration = hcpInteractions.reduce(
    (sum, i) => sum + (i.duration_minutes || 0),
    0
  );

  const followUpCount = hcpInteractions.filter(
    (i) => i.follow_up_required
  ).length;

  if (hcpLoading || !currentHcp) {
    return (
      <div className="page-container">
        <button className="back-button" onClick={() => navigate('/hcps')}>
          <FiArrowLeft /> Back to HCPs
        </button>
        <div className="loading-container">
          <div className="spinner" />
          <div className="loading-text">Loading HCP profile...</div>
        </div>
      </div>
    );
  }

  const name = currentHcp.name || currentHcp.full_name || 'Unknown';

  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <button className="back-button" onClick={() => navigate('/hcps')}>
        <FiArrowLeft /> Back to HCPs
      </button>

      {/* Profile Header */}
      <div className="hcp-detail-header">
        <div className="hcp-detail-avatar">{getInitials(name)}</div>
        <div className="hcp-detail-info">
          <h2>{name}</h2>
          <p>{currentHcp.specialty || 'General Practice'}</p>
          <div className="hcp-detail-meta">
            {currentHcp.tier && (
              <span className={`tier-badge ${getTierClass(currentHcp.tier)}`}>
                {String(currentHcp.tier).toUpperCase()}
              </span>
            )}
            {currentHcp.institution && (
              <span className="hcp-detail-meta-item">
                <FiBriefcase size={14} /> {currentHcp.institution}
              </span>
            )}
            {(currentHcp.city || currentHcp.location) && (
              <span className="hcp-detail-meta-item">
                <FiMapPin size={14} /> {currentHcp.city || currentHcp.location}
              </span>
            )}
            {currentHcp.email && (
              <span className="hcp-detail-meta-item">
                <FiMail size={14} /> {currentHcp.email}
              </span>
            )}
            {currentHcp.phone && (
              <span className="hcp-detail-meta-item">
                <FiPhone size={14} /> {currentHcp.phone}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Engagement Metrics */}
      <div className="hcp-detail-section" style={{ marginBottom: '24px' }}>
        <div className="hcp-detail-section-title">
          <FiTrendingUp size={18} style={{ color: 'var(--primary)' }} />
          Engagement Metrics
        </div>
        <div className="metrics-grid">
          <div className="metric-item">
            <div className="metric-value purple">{hcpInteractions.length}</div>
            <div className="metric-label">Total Interactions</div>
          </div>
          <div className="metric-item">
            <div className="metric-value teal">{totalDuration}</div>
            <div className="metric-label">Total Minutes</div>
          </div>
          <div className="metric-item">
            <div className="metric-value coral">{sentimentCounts.positive}</div>
            <div className="metric-label">Positive Engagements</div>
          </div>
          <div className="metric-item">
            <div className="metric-value amber">{followUpCount}</div>
            <div className="metric-label">Follow-ups</div>
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="hcp-detail-grid">
        {/* Interaction Timeline */}
        <div className="hcp-detail-section">
          <div className="hcp-detail-section-title">
            <FiActivity size={18} style={{ color: 'var(--primary)' }} />
            Interaction Timeline
          </div>
          {hcpInteractions.length > 0 ? (
            <div className="timeline">
              {hcpInteractions.slice(0, 10).map((interaction) => {
                const SentimentIcon =
                  interaction.sentiment === 'positive'
                    ? FiSmile
                    : interaction.sentiment === 'negative'
                    ? FiFrown
                    : FiMeh;

                return (
                  <div key={interaction.id} className="timeline-item">
                    <div className="timeline-dot" />
                    <div className="timeline-content">
                      <div className="timeline-title">
                        <span
                          className={`type-badge ${interaction.interaction_type || 'call'}`}
                          style={{ marginRight: '8px' }}
                        >
                          {interaction.interaction_type || 'call'}
                        </span>
                        {interaction.sentiment && (
                          <span
                            className={`sentiment-badge ${interaction.sentiment}`}
                          >
                            <SentimentIcon size={12} />
                          </span>
                        )}
                      </div>
                      <div className="timeline-description">
                        {interaction.ai_summary || interaction.raw_notes || 'No notes'}
                      </div>
                      <div className="timeline-date">
                        <FiCalendar
                          size={12}
                          style={{ marginRight: '4px', verticalAlign: 'middle' }}
                        />
                        {formatDate(
                          interaction.interaction_date ||
                            interaction.date ||
                            interaction.created_at
                        )}
                        {interaction.duration_minutes && (
                          <>
                            {' '}
                            ·{' '}
                            <FiClock
                              size={12}
                              style={{ marginRight: '2px', verticalAlign: 'middle' }}
                            />
                            {interaction.duration_minutes} min
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-state" style={{ padding: '30px' }}>
              <FiMessageSquare
                style={{ fontSize: '32px', color: 'var(--text-muted)', marginBottom: '8px' }}
              />
              <div className="empty-state-title">No interactions yet</div>
            </div>
          )}
        </div>

        {/* Product Affinity */}
        <div className="hcp-detail-section">
          <div className="hcp-detail-section-title">
            <FiTarget size={18} style={{ color: 'var(--primary)' }} />
            Product Affinity
          </div>
          {productAffinities.length > 0 ? (
            <div className="affinity-bars">
              {productAffinities.map(([product, count]) => (
                <div key={product} className="affinity-bar-item">
                  <div className="affinity-bar-header">
                    <span className="affinity-bar-label">{product}</span>
                    <span className="affinity-bar-value">
                      {count} mention{count !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="affinity-bar-track">
                    <motion.div
                      className="affinity-bar-fill"
                      initial={{ width: 0 }}
                      animate={{
                        width: `${(count / maxProductCount) * 100}%`,
                      }}
                      transition={{ duration: 1, delay: 0.3 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state" style={{ padding: '30px' }}>
              <FiTarget
                style={{ fontSize: '32px', color: 'var(--text-muted)', marginBottom: '8px' }}
              />
              <div className="empty-state-title">No product data</div>
              <div className="empty-state-description">
                Products will appear here once interactions mention them
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default HCPDetail;
