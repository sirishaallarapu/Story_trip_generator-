import React from 'react';
import './ItineraryDisplay.css';
import logo from '../assets/infologo1.png';

function ItineraryDisplay({ itinerary, vibe, destination = "Your Destination" }) {
  if (!itinerary) {
    return <p className="no-itinerary">Enter your details for your dream trip itinerary</p>;
  }

  const lines = itinerary.split('\n');
  const elements = [];

  lines.forEach((line, idx) => {
    const urlRegex = /(https?:\/\/[^\s]+)/;
    const match = line.match(urlRegex);

    if (match) {
      const url = match[0];
      const textBefore = line.replace(url, '').trim();

      elements.push(
        <p
          key={idx}
          className={
            line.startsWith('Accommodation:') || line.startsWith('Transport:')
              ? 'section'
              : line.startsWith('Total Cost:') || line.startsWith('Total Estimated Trip Cost:')
              ? 'total-cost'
              : line.startsWith('Activities:') || line.startsWith('Meals:')
              ? 'section-title'
              : line.startsWith('Day')
              ? 'day-heading'
              : 'item'
          }
        >
          {textBefore}{' '}
          <a href={url} target="_blank" rel="noopener noreferrer" className="book-link">
            Book Now
          </a>
        </p>
      );
    } else if (line.startsWith('Day')) {
      elements.push(
        <h3 key={idx} className="day-heading">
          {line}
        </h3>
      );
    } else if (
      line.startsWith('Transport:') ||
      line.startsWith('Accommodation:') ||
      line.startsWith('Total Cost:')
    ) {
      elements.push(
        <p key={idx} className="section">
          {line}
        </p>
      );
    } else if (line.startsWith('Activities:') || line.startsWith('Meals:')) {
      elements.push(
        <p key={idx} className="section-title">
          {line}
        </p>
      );
    } else if (line.trim().startsWith('-')) {
      elements.push(
        <p key={idx} className="item">
          {line.trim()}
        </p>
      );
    } else if (line.startsWith('Total Estimated Trip Cost:')) {
      elements.push(
        <p key={idx} className="total-cost">
          {line}
        </p>
      );
    }
  });

  // Function to call backend API and download PDF
  async function handleDownloadPDF() {
    try {
      const response = await fetch('http://localhost:8000/api/generate-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ itinerary, vibe, destination }),
      });

      if (!response.ok) {
        alert('Failed to generate PDF');
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `trip_itinerary.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Error occurred while downloading PDF');
    }
  }

  return (
    <div className="itinerary-container">
      <div className="itinerary-header">
        <h2 className="itinerary-title">Your Trip Itinerary</h2>
        {vibe && <p className="vibe">Vibe: {vibe}</p>}
      </div>

      <div className="itinerary-body">
        <div className="itinerary-text">{elements}</div>
      </div>

      <div className="itinerary-footer">
        <button className="pdf-button" onClick={handleDownloadPDF}>
          📄 Download PDF
        </button>
      </div>
    </div>
  );
}

export default ItineraryDisplay;
