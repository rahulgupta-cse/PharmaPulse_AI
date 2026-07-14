import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiHome,
  FiUsers,
  FiMessageSquare,
  FiCalendar,
  FiTrendingUp,
  FiPlus,
  FiSearch,
  FiActivity,
  FiClock,
  FiArrowRight,
} from 'react-icons/fi';
import { fetchInteractions } from '../store/slices/interactionSlice';
import { fetchHCPs } from '../store/slices/hcpSlice';
import { format, parseISO, isThisWeek } from 'date-fns';

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

function Dashboard() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { interactions } = useSelector((state) => state.interactions);
  const { hcps } = useSelector((state) => state.hcps);
  const [stats, setStats] = useState({
    totalHcps: 0,
    totalInteractions: 0,
    thisWeek: 0,
    followUps: 0,
  });

  useEffect(() => {
    dispatch(fetchInteractions({}));
    dispatch(fetchHCPs({}));
  }, [dispatch]);

  useEffect(() => {
    const thisWeekCount = interactions.filter((i) => {
      try {
        return isThisWeek(parseISO(i.interaction_date || i.date || i.created_at));
      } catch {
        return false;
      }
    }).length;

    const followUpCount = interactions.filter(
      (i) => i.follow_up_required || i.followup_required
    ).length;

    setStats({
      totalHcps: hcps.length,
      totalInteractions: interactions.length,
      thisWeek: thisWeekCount,
      followUps: followUpCount,
    });
  }, [interactions, hcps]);

  const recentInteractions = interactions.slice(0, 5);

  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatDate = (dateStr) => {
    try {
      return format(parseISO(dateStr), 'MMM d, yyyy');
    } catch {
      return dateStr || 'N/A';
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
      {/* Welcome Card */}
      <div className="dashboard-welcome">
        <h2>
          Welcome back, <span>Agent</span>
        </h2>
        <p>
          Manage your HCP interactions with AI-powered insights. Track engagements,
          analyze sentiment, and optimize your outreach strategy.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="dashboard-stats">
        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="stat-card-header">
            <div className="stat-card-icon purple">
              <FiUsers />
            </div>
            <span className="stat-card-trend up">+12%</span>
          </div>
          <div className="stat-card-value">{stats.totalHcps}</div>
          <div className="stat-card-label">Total HCPs</div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="stat-card-header">
            <div className="stat-card-icon teal">
              <FiMessageSquare />
            </div>
            <span className="stat-card-trend up">+8%</span>
          </div>
          <div className="stat-card-value">{stats.totalInteractions}</div>
          <div className="stat-card-label">Total Interactions</div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="stat-card-header">
            <div className="stat-card-icon coral">
              <FiCalendar />
            </div>
          </div>
          <div className="stat-card-value">{stats.thisWeek}</div>
          <div className="stat-card-label">This Week</div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="stat-card-header">
            <div className="stat-card-icon amber">
              <FiClock />
            </div>
          </div>
          <div className="stat-card-value">{stats.followUps}</div>
          <div className="stat-card-label">Follow-ups Due</div>
        </motion.div>
      </div>

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Recent Interactions */}
        <div className="glass-card-static">
          <div className="dashboard-section-title">
            <FiActivity className="icon" /> Recent Interactions
          </div>
          {recentInteractions.length > 0 ? (
            <div className="recent-interactions-list">
              {recentInteractions.map((interaction) => {
                const hcpName =
                  interaction.hcp_name ||
                  interaction.hcp?.name ||
                  `HCP #${interaction.hcp_id || '?'}`;
                return (
                  <div
                    key={interaction.id}
                    className="recent-interaction-item"
                    onClick={() => navigate('/interactions')}
                  >
                    <div className="recent-interaction-avatar">
                      {getInitials(hcpName)}
                    </div>
                    <div className="recent-interaction-info">
                      <div className="recent-interaction-name">{hcpName}</div>
                      <div className="recent-interaction-meta">
                        <span
                          className={`type-badge ${interaction.interaction_type || 'call'}`}
                        >
                          {interaction.interaction_type || 'call'}
                        </span>
                        {interaction.sentiment && (
                          <span
                            className={`sentiment-badge ${interaction.sentiment}`}
                          >
                            {interaction.sentiment}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="recent-interaction-date">
                      {formatDate(
                        interaction.interaction_date ||
                          interaction.date ||
                          interaction.created_at
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">
                <FiMessageSquare />
              </div>
              <div className="empty-state-title">No interactions yet</div>
              <div className="empty-state-description">
                Start by logging your first HCP interaction
              </div>
              <Link to="/log-interaction" className="btn btn-primary">
                <FiPlus /> Log Interaction
              </Link>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="glass-card-static">
          <div className="dashboard-section-title">
            <FiTrendingUp className="icon" /> Quick Actions
          </div>
          <div className="quick-actions-grid">
            <Link to="/log-interaction" className="quick-action-btn">
              <span className="icon purple">
                <FiPlus />
              </span>
              Log New Interaction
              <FiArrowRight
                style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}
              />
            </Link>
            <Link to="/hcps" className="quick-action-btn">
              <span className="icon teal">
                <FiUsers />
              </span>
              Browse HCP Profiles
              <FiArrowRight
                style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}
              />
            </Link>
            <Link to="/interactions" className="quick-action-btn">
              <span className="icon coral">
                <FiSearch />
              </span>
              Search Interactions
              <FiArrowRight
                style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}
              />
            </Link>
            <Link to="/log-interaction" className="quick-action-btn">
              <span className="icon amber">
                <FiMessageSquare />
              </span>
              Chat with AI Agent
              <FiArrowRight
                style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}
              />
            </Link>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default Dashboard;
