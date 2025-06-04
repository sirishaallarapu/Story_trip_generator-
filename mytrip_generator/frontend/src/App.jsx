import { useState } from 'react';
import Sidebar from './components/Sidebar';
import ItineraryDisplay from './components/ItineraryDisplay';
import logo from './assets/info.webp';
import './index.css';

function App() {
  const [itinerary, setItinerary] = useState('');
  const [vibe, setVibe] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (response) => {
    console.log('Setting itinerary:', response.itinerary);
    console.log('Setting vibe:', response.vibe);
    setItinerary(response.itinerary || '');
    setVibe(response.vibe || '');
    setError('');
  };

  const handleError = (err) => {
    let errorMsg = 'An error occurred. Please try again.';
    if (typeof err === 'string') {
      errorMsg = err;
    } else if (err?.response?.data?.detail) {
      const detail = err.response.data.detail;
      if (Array.isArray(detail)) {
        errorMsg = detail.map((e) => e.msg).join('; ');
      } else if (typeof detail === 'string') {
        errorMsg = detail;
      } else {
        errorMsg = 'Invalid input. Please check your form.';
      }
    } else if (err?.response?.data?.error) {
      errorMsg = err.response.data.error;
    } else if (err?.message) {
      errorMsg = err.message;
    }
    console.error('Error set:', errorMsg);
    setError(errorMsg);
    setItinerary('');
    setVibe('');
  };

  return (
    <div className="container">
      <Sidebar onSubmit={handleSubmit} onError={handleError} />
      <div className="main-content">
        <header className="header">
          <img src={logo} alt="Trip Generator Logo" />
          <h1>Story-Based Trip Generator</h1>
        </header>
        {error && <p className="error">{error}</p>}
        <ItineraryDisplay itinerary={itinerary} vibe={vibe} />
      </div>
    </div>
  );
}

export default App;