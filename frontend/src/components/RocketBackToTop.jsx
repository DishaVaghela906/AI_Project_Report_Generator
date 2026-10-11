import React, { useState, useEffect } from 'react';

export default function RocketBackToTop() {
  const [isVisible, setIsVisible] = useState(false);
  const [isLaunching, setIsLaunching] = useState(false);

  useEffect(() => {
    const toggleVisibility = () => {
      if (window.scrollY > 160) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };

    window.addEventListener('scroll', toggleVisibility, { passive: true });
    toggleVisibility();

    return () => window.removeEventListener('scroll', toggleVisibility);
  }, []);

  const handleLaunch = () => {
    setIsLaunching(true);
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });

    setTimeout(() => {
      setIsLaunching(false);
    }, 900);
  };

  if (!isVisible) return null;

  return (
    <button
      type="button"
      className={`rocket-back-to-top ${isLaunching ? 'launching' : ''}`}
      onClick={handleLaunch}
      aria-label="Back to top"
      title="Back to top"
    >
      <div className="rocket-img-container">
        <img 
          src="/back_to_top.png" 
          alt="Back to top" 
          className="rocket-icon-img"
        />
      </div>
      <div className="rocket-flame-glow" aria-hidden="true"></div>
      <span className="rocket-tooltip">Back to top</span>
    </button>
  );
}
