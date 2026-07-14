import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiHome,
  FiMessageSquare,
  FiList,
  FiUsers,
  FiZap,
  FiActivity,
} from 'react-icons/fi';

const navItems = [
  { path: '/', label: 'Dashboard', icon: FiHome },
  { path: '/log-interaction', label: 'Log Interaction', icon: FiMessageSquare },
  { path: '/interactions', label: 'Interactions', icon: FiList },
  { path: '/hcps', label: 'HCPs', icon: FiUsers },
];

function Sidebar() {
  const location = useLocation();

  return (
    <motion.aside
      className="sidebar"
      initial={{ x: -280 }}
      animate={{ x: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 20 }}
    >
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          <FiZap size={24} />
        </div>
        <div className="sidebar-brand-text">
          <h1>PharmaPulse AI CRM</h1>
          <span>HCP Module</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <ul>
          {navItems.map((item) => {
            const isActive =
              item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path);

            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                >
                  {isActive && (
                    <motion.div
                      className="sidebar-nav-indicator"
                      layoutId="sidebar-indicator"
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                  <item.icon size={20} className="sidebar-nav-icon" />
                  <span>{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Status Card */}
      <div className="sidebar-status">
        <div className="sidebar-status-card">
          <div className="sidebar-status-dot" />
          <div className="sidebar-status-info">
            <span className="sidebar-status-label">AI Agent</span>
            <span className="sidebar-status-value">
              <FiActivity size={12} /> Online
            </span>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}

export default Sidebar;
