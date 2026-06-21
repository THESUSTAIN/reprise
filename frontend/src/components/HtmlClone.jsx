import React from 'react';

/**
 * Renders the original OkyAI HTML page inside an iframe.
 * No invention, no modification — only a Zayado palette CSS override
 * has been injected into the static HTML files in /public/okyai-clone/.
 */
const HtmlClone = ({ src, title, testId }) => {
  return (
    <iframe
      src={src}
      title={title}
      data-testid={testId || 'html-clone-iframe'}
      style={{
        position: 'fixed',
        inset: 0,
        width: '100vw',
        height: '100vh',
        border: 'none',
      }}
    />
  );
};

export default HtmlClone;
