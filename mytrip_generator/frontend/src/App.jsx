import React, { useState } from 'react';
import './App.css';
import TripForm from './components/TripForm';

function App() {
  const [itineraryData, setItineraryData] = useState(null);
  const [formDetails, setFormDetails] = useState(null);

  const handleItinerarySubmit = (data, formData) => {
    setItineraryData(data);
    setFormDetails(formData);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Story-Based Trip Generator</h1>
      </header>
      <main className="main-container">
        <div className="left-panel">
          <h2>Plan Your Trip</h2>
          <TripForm onSubmit={(data) => handleItinerarySubmit(data, {
            prompt: data.prompt,
            budget: data.budget,
            restrictions: data.restrictions,
            tripDuration: data.trip_duration
          })} />
          {formDetails && (
            <div className="trip-details">
              <h3>Trip Details</h3>
              <p><strong>Destination:</strong> {formDetails.prompt}</p>
              <p><strong>Budget:</strong> ₹{formDetails.budget}</p>
              <p><strong>Restrictions:</strong> {formDetails.restrictions || 'None'}</p>
              <p><strong>Duration:</strong> {formDetails.tripDuration} days</p>
            </div>
          )}
        </div>
        <div className="right-panel">
          {itineraryData ? (
            <div className="itinerary-container">
              <h2>Your Adventure Itinerary</h2>
              <div className="vibe-section">
                <h3>Vibe</h3>
                <p>{itineraryData.vibe_description || 'A thrilling adventure awaits!'}</p>
              </div>
              {itineraryData.itinerary && itineraryData.itinerary.map((day) => (
                <div key={day.day} className="day-section">
                  <h3>Day {day.day} - {day.destination}</h3>
                  <p>{day.description}</p>
                  <h4>Activities:</h4>
                  <ul>
                    {day.activities.map((activity, index) => (
                      <li key={index}>{activity}</li>
                    ))}
                  </ul>
                  <p><strong>Transport:</strong> {day.transport}</p>
                  <p><strong>Tip:</strong> {day.tip}</p>
                  <h4>Budget:</h4>
                  <ul>
                    <li>Accommodation: ₹{day.daily_budget.accommodation}</li>
                    <li>Food: ₹{day.daily_budget.food}</li>
                    <li>Activities: ₹{day.daily_budget.activities}</li>
                    <li>Transport: ₹{day.daily_budget.transport}</li>
                  </ul>
                </div>
              ))}
              <div className="recommendations-section">
                <h3>Recommendations</h3>
                {itineraryData.recommendations && itineraryData.recommendations.length > 0 ? (
                  itineraryData.recommendations.map((rec, index) => (
                    <div key={index} className="recommendation">
                      {rec.stay && (
                        <div>
                          <h4>Stay: {rec.stay.name}</h4>
                          <p>{rec.stay.description}</p>
                          <p><strong>Price per Night:</strong> {rec.stay.price_per_night}</p>
                          <p><strong>Location:</strong> {rec.stay.island}</p>
                          <a href={rec.stay.booking_url} target="_blank" rel="noopener noreferrer">Book Now</a>
                        </div>
                      )}
                      {rec.activity && (
                        <div>
                          <h4>Activity: {rec.activity.name}</h4>
                          <p>{rec.activity.description}</p>
                          <p><strong>Cost:</strong> {rec.activity.cost}</p>
                          <p><strong>Location:</strong> {rec.activity.island}</p>
                          <a href={rec.activity.booking_url} target="_blank" rel="noopener noreferrer">Book Now</a>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p>No recommendations available.</p>
                )}
              </div>
              <div className="summary-section">
                <h3>Summary</h3>
                <p>{itineraryData.text_itinerary}</p>
                {itineraryData.budget_summary && (
                  <div>
                    <p><strong>Total Spent:</strong> ₹{itineraryData.budget_summary.total_spent}</p>
                    <p><strong>Remaining:</strong> ₹{itineraryData.budget_summary.remaining}</p>
                    {itineraryData.budget_summary.exceeded > 0 && (
                      <p><strong>Exceeded:</strong> ₹{itineraryData.budget_summary.exceeded}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p>Submit a trip plan to see your itinerary.</p>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;