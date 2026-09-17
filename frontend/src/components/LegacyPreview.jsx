import React, { useEffect, useRef } from "react";
import { Helmet } from "react-helmet-async";

/**
 * LegacyPreview — Strictly preserves the rendering of app-main static HTML pages.
 * The HTML/CSS/JS lives in /public/preview/*.html (copied from /app/_legacy/app-main/frontend/public/preview/).
 * Renders as a full-bleed iframe so its embedded nav, modals and scripts work as-is.
 */
export default function LegacyPreview({ src, title, description }) {
  const iframeRef = useRef(null);

  useEffect(() => {
    // Resize the iframe to fill viewport height (minus any scrollbars).
    const adjust = () => {
      if (iframeRef.current) {
        iframeRef.current.style.height = window.innerHeight + "px";
      }
    };
    adjust();
    window.addEventListener("resize", adjust);
    return () => window.removeEventListener("resize", adjust);
  }, []);

  return (
    <>
      <Helmet>
        <title>{title}</title>
        {description && <meta name="description" content={description} />}
      </Helmet>
      <iframe
        ref={iframeRef}
        src={src}
        title={title}
        data-testid="legacy-preview-iframe"
        style={{
          width: "100%",
          border: "none",
          display: "block",
          background: "white",
        }}
      />
    </>
  );
}
