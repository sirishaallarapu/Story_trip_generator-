import { useState } from 'react';
import axios from 'axios';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './sidebar.css';

function Sidebar({ onSubmit, onError }) {
  const [formData, setFormData] = useState({
    destination: '',
    trip_type: '',
    food_preference: '',
    num_members: 1,
    budget: 'medium',
    start_date: null,
    end_date: null,
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      let duration = 0;
      if (formData.start_date && formData.end_date) {
        const start = new Date(formData.start_date);
        const end = new Date(formData.end_date);
        duration = Math.floor((end - start) / (1000 * 60 * 60 * 24)) + 1;
        if (duration <= 0) {
          throw new Error('End date must be after start date.');
        }
      } else {
        throw new Error('Please select valid start and end dates.');
      }

      const payload = {
        destination: formData.destination,
        trip_type: formData.trip_type,
        food_preference: formData.food_preference,
        num_members: parseInt(formData.num_members),
        budget: formData.budget,
        start_date: formData.start_date?.toISOString(),
        end_date: formData.end_date?.toISOString(),
        duration: duration,
      };

      console.log('Payload sent to /api/trip:', JSON.stringify(payload, null, 2));

      const response = await axios.post('http://localhost:8000/api/trip', payload);
      console.log('API response:', JSON.stringify(response.data, null, 2));
      onSubmit(response.data);
    } catch (err) {
      console.error('Submission error:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
      });
      onError(err);
    } finally {
      setLoading(false);
    }
  };

  const today = new Date();

  return (
    <aside className="sidebar">
      <h2 className="sidebar-title">Plan Your Trip</h2>
      <form className="trip-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Destination</label>
          <input
            type="text"
            name="destination"
            value={formData.destination}
            onChange={handleChange}
            className="form-input"
            required
            placeholder="e.g., Maldives"
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label>Trip Type</label>
          <select
            name="trip_type"
            value={formData.trip_type}
            onChange={handleChange}
            className="form-input"
            required
            disabled={loading}
          >
            <option value="">Select</option>
            <option value="beach">Beach</option>
            <option value="romantic">Romantic</option>
            <option value="adventure">Adventure</option>
            <option value="cultural">Cultural</option>
          </select>
        </div>
        <div className="form-group">
          <label>Food Preference</label>
          <select
            name="food_preference"
            value={formData.food_preference}
            onChange={handleChange}
            className="form-input"
            required
            disabled={loading}
          >
            <option value="">Select</option>
            <option value="veg">Vegetarian</option>
            <option value="non_veg">Non-Vegetarian</option>
          </select>
        </div>
        <div className="form-group">
          <label>Number of Members</label>
          <input
            type="number"
            name="num_members"
            value={formData.num_members}
            onChange={handleChange}
            className="form-input"
            required
            min="1"
            placeholder="e.g., 2"
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label>Budget</label>
          <select
            name="budget"
            value={formData.budget}
            onChange={handleChange}
            className="form-input"
            required
            disabled={loading}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        <div className="form-group">
          <label>Start Date</label>
          <DatePicker
            selected={formData.start_date}
            onChange={(date) => setFormData({ ...formData, start_date: date })}
            dateFormat="yyyy-MM-dd"
            className="form-input"
            minDate={today}
            required
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label>End Date</label>
          <DatePicker
            selected={formData.end_date}
            onChange={(date) => setFormData({ ...formData, end_date: date })}
            dateFormat="yyyy-MM-dd"
            className="form-input"
            minDate={formData.start_date || today}
            required
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? 'Generating...' : 'Generate Itinerary'}
          </button>
        </div>
      </form>
    </aside>
  );
}

export default Sidebar;