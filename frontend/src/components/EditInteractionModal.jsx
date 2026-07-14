import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import {
  FiX,
  FiCheck,
  FiPhone,
  FiMail,
  FiBriefcase,
  FiUsers,
  FiMonitor,
  FiCalendar,
  FiClock,
  FiSmile,
  FiMeh,
  FiFrown,
  FiPlus,
} from 'react-icons/fi';
import { updateInteraction } from '../store/slices/interactionSlice';
import { format, parseISO } from 'date-fns';

const INTERACTION_TYPES = [
  { value: 'call', label: 'Call', icon: FiPhone },
  { value: 'email', label: 'Email', icon: FiMail },
  { value: 'visit', label: 'Visit', icon: FiBriefcase },
  { value: 'conference', label: 'Conference', icon: FiUsers },
  { value: 'virtual', label: 'Virtual', icon: FiMonitor },
];

function EditInteractionModal({ interaction, onClose }) {
  const dispatch = useDispatch();
  const [saving, setSaving] = useState(false);
  const [productInput, setProductInput] = useState('');

  const [form, setForm] = useState({
    interaction_type: interaction.interaction_type || 'call',
    interaction_date: '',
    duration_minutes: interaction.duration_minutes || 30,
    raw_notes: interaction.raw_notes || '',
    products_discussed: interaction.products_discussed || [],
    sentiment: interaction.sentiment || '',
    follow_up_required: interaction.follow_up_required || false,
    follow_up_date: '',
    follow_up_notes: interaction.follow_up_notes || '',
  });

  useEffect(() => {
    // Parse dates safely
    let interactionDate = '';
    try {
      const dateField =
        interaction.interaction_date || interaction.date || interaction.created_at;
      if (dateField) {
        interactionDate = format(parseISO(dateField), 'yyyy-MM-dd');
      }
    } catch {
      interactionDate = '';
    }

    let followUpDate = '';
    try {
      if (interaction.follow_up_date) {
        followUpDate = format(parseISO(interaction.follow_up_date), 'yyyy-MM-dd');
      }
    } catch {
      followUpDate = '';
    }

    setForm((prev) => ({
      ...prev,
      interaction_date: interactionDate,
      follow_up_date: followUpDate,
    }));
  }, [interaction]);

  const handleChange = (field, value) => {
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

  const handleSave = async () => {
    setSaving(true);
    try {
      await dispatch(
        updateInteraction({
          id: interaction.id,
          data: {
            ...form,
            duration_minutes: parseInt(form.duration_minutes) || 0,
            follow_up_date: form.follow_up_required
              ? form.follow_up_date || undefined
              : undefined,
            follow_up_notes: form.follow_up_required
              ? form.follow_up_notes || undefined
              : undefined,
          },
        })
      ).unwrap();
      toast.success('Interaction updated');
      onClose();
    } catch (err) {
      toast.error(err || 'Failed to update');
    } finally {
      setSaving(false);
    }
  };

  // Stop clicks from propagating to overlay
  const handleContentClick = (e) => {
    e.stopPropagation();
  };

  return (
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="modal-content"
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        onClick={handleContentClick}
      >
        {/* Header */}
        <div className="modal-header">
          <h3>Edit Interaction</h3>
          <button className="modal-close" onClick={onClose}>
            <FiX />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
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
                  onClick={() => handleChange('interaction_type', type.value)}
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
                onChange={(e) => handleChange('interaction_date', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">
                <FiClock size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                Duration (min)
              </label>
              <input
                type="number"
                className="form-input"
                min="1"
                max="480"
                value={form.duration_minutes}
                onChange={(e) => handleChange('duration_minutes', e.target.value)}
              />
            </div>
          </div>

          {/* Notes */}
          <div className="form-group">
            <label className="form-label">Notes</label>
            <textarea
              className="form-textarea"
              rows={4}
              value={form.raw_notes}
              onChange={(e) => handleChange('raw_notes', e.target.value)}
            />
          </div>

          {/* Products */}
          <div className="form-group">
            <label className="form-label">Products Discussed</label>
            <div className="product-input-row">
              <input
                type="text"
                className="form-input"
                placeholder="Add product"
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
                onClick={() => handleChange('sentiment', 'positive')}
              >
                <FiSmile /> Positive
              </div>
              <div
                className={`sentiment-option neutral ${
                  form.sentiment === 'neutral' ? 'selected' : ''
                }`}
                onClick={() => handleChange('sentiment', 'neutral')}
              >
                <FiMeh /> Neutral
              </div>
              <div
                className={`sentiment-option negative ${
                  form.sentiment === 'negative' ? 'selected' : ''
                }`}
                onClick={() => handleChange('sentiment', 'negative')}
              >
                <FiFrown /> Negative
              </div>
            </div>
          </div>

          {/* Follow-up */}
          <div className="form-group">
            <div className="toggle-container">
              <div
                className={`toggle-switch ${
                  form.follow_up_required ? 'active' : ''
                }`}
                onClick={() =>
                  handleChange('follow_up_required', !form.follow_up_required)
                }
              >
                <div className="toggle-switch-knob" />
              </div>
              <span className="toggle-label">Follow-up required</span>
            </div>

            {form.follow_up_required && (
              <div className="followup-section">
                <div className="form-row">
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Follow-up Date</label>
                    <input
                      type="date"
                      className="form-input"
                      value={form.follow_up_date}
                      onChange={(e) =>
                        handleChange('follow_up_date', e.target.value)
                      }
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Follow-up Notes</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Follow-up action"
                      value={form.follow_up_notes}
                      onChange={(e) =>
                        handleChange('follow_up_notes', e.target.value)
                      }
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? (
              <>
                <span className="spinner spinner-inline" /> Saving...
              </>
            ) : (
              <>
                <FiCheck /> Save Changes
              </>
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default EditInteractionModal;
