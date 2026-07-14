import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiSearch,
  FiUser,
  FiMapPin,
  FiBriefcase,
  FiMessageSquare,
  FiArrowRight,
} from 'react-icons/fi';
import { fetchHCPs, setHcpFilters } from '../store/slices/hcpSlice';

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.05, duration: 0.3, ease: [0.4, 0, 0.2, 1] },
  }),
};

function HCPList() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { hcps, loading, error, filters } = useSelector((state) => state.hcps);

  useEffect(() => {
    dispatch(fetchHCPs({}));
  }, [dispatch]);

  const handleFilterChange = (field, value) => {
    dispatch(setHcpFilters({ [field]: value }));
  };

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

  const getTierLabel = (tier) => {
    if (!tier) return 'Tier 3';
    return String(tier).toUpperCase();
  };

  // Client-side filter
  const filtered = hcps.filter((hcp) => {
    const name = (hcp.name || hcp.full_name || '').toLowerCase();
    const specialty = (hcp.specialty || '').toLowerCase();
    if (filters.search && !name.includes(filters.search.toLowerCase()) && !specialty.includes(filters.search.toLowerCase())) {
      return false;
    }
    if (filters.specialty && (hcp.specialty || '').toLowerCase() !== filters.specialty.toLowerCase()) {
      return false;
    }
    if (filters.tier && String(hcp.tier || '') !== filters.tier) {
      return false;
    }
    return true;
  });

  // Unique specialties for filter
  const specialties = [...new Set(hcps.map((h) => h.specialty).filter(Boolean))];
  const tiers = [...new Set(hcps.map((h) => h.tier).filter(Boolean))];

  return (
    <motion.div
      className="page-container"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <div className="page-header">
        <h2>Healthcare Professionals</h2>
        <p>Manage your HCP database and view engagement profiles</p>
      </div>

      {/* Filters */}
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
            placeholder="Search by name or specialty..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            style={{ paddingLeft: '40px', width: '100%' }}
          />
        </div>
        {specialties.length > 0 && (
          <select
            className="form-select"
            value={filters.specialty}
            onChange={(e) => handleFilterChange('specialty', e.target.value)}
          >
            <option value="">All Specialties</option>
            {specialties.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        )}
        {tiers.length > 0 && (
          <select
            className="form-select"
            value={filters.tier}
            onChange={(e) => handleFilterChange('tier', e.target.value)}
          >
            <option value="">All Tiers</option>
            {tiers.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Loading */}
      {loading && hcps.length === 0 ? (
        <div className="loading-container">
          <div className="spinner" />
          <div className="loading-text">Loading HCPs...</div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <FiUser />
          </div>
          <div className="empty-state-title">No HCPs found</div>
          <div className="empty-state-description">
            {filters.search || filters.specialty || filters.tier
              ? 'Try adjusting your filters'
              : 'No healthcare professionals in the database'}
          </div>
        </div>
      ) : (
        <div className="hcp-grid">
          {filtered.map((hcp, i) => {
            const name = hcp.name || hcp.full_name || 'Unknown';
            return (
              <motion.div
                key={hcp.id}
                className="hcp-card"
                custom={i}
                variants={cardVariants}
                initial="hidden"
                animate="visible"
                onClick={() => navigate(`/hcps/${hcp.id}`)}
              >
                <div className="hcp-card-header">
                  <div className="hcp-card-avatar">{getInitials(name)}</div>
                  <div>
                    <div className="hcp-card-name">{name}</div>
                    <div className="hcp-card-specialty">
                      {hcp.specialty || 'General Practice'}
                    </div>
                  </div>
                  {hcp.tier && (
                    <span
                      className={`tier-badge ${getTierClass(hcp.tier)}`}
                      style={{ marginLeft: 'auto' }}
                    >
                      {getTierLabel(hcp.tier)}
                    </span>
                  )}
                </div>

                <div className="hcp-card-body">
                  {hcp.institution && (
                    <div className="hcp-card-detail">
                      <FiBriefcase size={14} className="icon" />
                      {hcp.institution}
                    </div>
                  )}
                  {(hcp.city || hcp.location) && (
                    <div className="hcp-card-detail">
                      <FiMapPin size={14} className="icon" />
                      {hcp.city || hcp.location}
                    </div>
                  )}
                  {hcp.email && (
                    <div className="hcp-card-detail">
                      <FiUser size={14} className="icon" />
                      {hcp.email}
                    </div>
                  )}
                </div>

                <div className="hcp-card-footer">
                  <div className="hcp-card-interactions">
                    <FiMessageSquare
                      size={14}
                      style={{ marginRight: '6px', verticalAlign: 'middle' }}
                    />
                    <strong>{hcp.interaction_count || 0}</strong> interactions
                  </div>
                  <FiArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}

export default HCPList;
