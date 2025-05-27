import React, { useState } from 'react';
import axios from 'axios';
import './TripForm.css';

const TripForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    prompt: '',
    budget: 50000,
    restrictions: 'vegetarian meals only',
    tripDuration: 5
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') e.preventDefault();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    console.log('Form payload:', formData);

    try {
      const payload = {
        prompt: formData.prompt.trim(),
        budget: parseFloat(formData.budget),
        restrictions: formData.restrictions,
        trip_duration: parseInt(formData.tripDuration)
      };
      const source = axios.CancelToken.source();
      const timeout = setTimeout(() => {
        source.cancel('Request timed out after 90 seconds. Check if the server is running on port 8000 or if OpenAI API is delayed.');
      }, 90000);

      const res = await axios.post('http://localhost:8000/api/generate-itinerary', payload, {
        cancelToken: source.token,
        timeout: 90000
      });
      clearTimeout(timeout);
      onSubmit(res.data, formData); // Pass formData
    } catch (err) {
      if (axios.isCancel(err)) {
        setError(err.message);
      } else if (err.code === 'ECONNREFUSED') {
        setError('Cannot connect to server. Ensure FastAPI is running on http://localhost:8000.');
      } else if (err.code === 'ECONNABORTED') {
        setError('Request timed out. The server or OpenAI API may be slow. Try again or check rate limits.');
      } else {
        setError(err.response?.data?.detail || err.message || 'An error occurred while generating the itinerary.');
      }
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="trip-form-container">
      <form onSubmit={handleSubmit} className="trip-form">
        <div className="form-group">
          <label>Describe Your Trip</label>
          <input
            type="text"
            name="prompt"
            value={formData.prompt}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            className="form-input"
            placeholder="e.g., Adventure trip in Maldives"
            required
            autoComplete="off"
          />
        </div>
        <div className="form-group">
          <label>Budget (INR)</label>
          <input
            type="number"
            name="budget"
            value={formData.budget}
            onChange={handleChange}
            className="form-input"
            required
          />
        </div>
        <div className="form-group">
          <label>Restrictions</label>
          <input
            type="text"
            name="restrictions"
            value={formData.restrictions}
            onChange={handleChange}
            className="form-input"
            placeholder="e.g., vegetarian meals only"
          />
        </div>
        <div className="form-group">
          <label>Trip Duration (days)</label>
          <input
            type="number"
            name="tripDuration"
            value={formData.tripDuration}
            onChange={handleChange}
            className="form-input"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="submit-button"
        >
          {loading ? 'Generating...' : 'Generate Itinerary'}
        </button>
      </form>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default TripForm;