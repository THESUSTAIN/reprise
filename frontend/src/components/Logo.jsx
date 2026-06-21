import React from 'react';

/**
 * Brand logo "MyExtension-ai by Zayado" — version officielle (portée de final-main).
 * SVG inline, transparent. Trois tailles disponibles.
 *
 *   variant="onDark"  → bars cream — sur fond navy / sombre (header en dark mode)
 *   variant="onLight" → bars navy — sur fond cream / clair
 */
export default function Logo({
  variant = 'onLight',
  size = 'md',
  showWordmark = true,
  className = '',
  testid = 'brand-logo',
}) {
  const sizes = {
    sm: { iconPx: 18, text: 'text-[12.5px]', sep: 'text-[14px]', gap: 'gap-1.5', byText: 'text-[9px]' },
    md: { iconPx: 22, text: 'text-[13.5px]', sep: 'text-[15px]', gap: 'gap-2',   byText: 'text-[10px]' },
    lg: { iconPx: 34, text: 'text-[20px]',   sep: 'text-[22px]', gap: 'gap-2.5', byText: 'text-[11px]' },
  };
  const s = sizes[size] || sizes.md;
  const isDark = variant === 'onDark';

  const barColor = isDark ? '#f6f3ee' : '#102945';
  const arrowColor = '#c8302b';
  const accent = '#d4b982';

  const textColor = isDark ? 'text-[#f6f3ee]' : 'text-[#102945]';
  const brandColor = isDark ? 'text-[#f6f3ee]/70' : 'text-[#102945]/65';
  const aiAccent = isDark ? 'text-[#d4b982]' : 'text-[#9c7d40]';

  return (
    <span
      className={`inline-flex items-center ${s.gap} ${className}`}
      data-testid={testid}
    >
      <svg
        width={s.iconPx}
        height={s.iconPx}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="MyExtension AI"
        className="shrink-0"
      >
        <rect x="6" y="14" width="38" height="7.5" rx="2" fill={barColor} />
        <rect x="6" y="28" width="30" height="7.5" rx="2" fill={barColor} />
        <rect x="6" y="42" width="22" height="7.5" rx="2" fill={barColor} />
        <path d="M30 42 L40 42 L36 49.5 L28 49.5 Z" fill={accent} />
        <path
          d="M12 56 C 26 50, 38 38, 50 18 L 46 22 M 50 18 L 54 22"
          stroke={arrowColor}
          strokeWidth="5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </svg>
      {showWordmark && (
        <span className="inline-flex items-center gap-1.5 leading-none">
          <span
            className={`${s.text} ${textColor} font-serif font-normal tracking-tight whitespace-nowrap`}
            style={{ fontFamily: '"Playfair Display", Georgia, serif' }}
          >
            MyExtension<span className={aiAccent}>-ai</span>
          </span>
          <span
            className={`${s.byText} ${brandColor} font-light italic whitespace-nowrap`}
            style={{ fontFamily: '"Playfair Display", Georgia, serif' }}
          >
            by Zayado
          </span>
        </span>
      )}
    </span>
  );
}
