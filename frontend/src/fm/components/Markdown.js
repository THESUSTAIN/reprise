import React from "react";

/**
 * Mini-renderer Markdown sans dépendance externe.
 * Gère :
 *   - **gras**            → <strong>
 *   - *italique* ou _it_  → <em>
 *   - `inline code`       → <code>
 *   - Listes - item       → <ul><li>
 *   - Listes 1. item      → <ol><li>
 *   - Liens [text](url)   → <a>
 *   - Sauts de ligne      → paragraphes
 *
 * NB : pas de support des tableaux, headings, blockquotes ou code blocks.
 *      Suffisant pour Claude Sonnet en mode chat conversationnel.
 */
function renderInline(text) {
  // Échapper le HTML brut pour éviter toute injection
  let safe = String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Liens [text](url) — d'abord pour ne pas casser les *
  safe = safe.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_m, t, u) =>
    `<a href="${u}" target="_blank" rel="noopener noreferrer" style="color:#1a3a6e;text-decoration:underline">${t}</a>`
  );

  // Gras **text**
  safe = safe.replace(/\*\*([^*\n]+?)\*\*/g, "<strong>$1</strong>");

  // Italique *text* ou _text_
  safe = safe.replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, "$1<em>$2</em>");
  safe = safe.replace(/(^|[^_])_([^_\n]+?)_(?!_)/g, "$1<em>$2</em>");

  // Code inline `code`
  safe = safe.replace(
    /`([^`\n]+?)`/g,
    '<code style="background:rgba(184,152,85,0.12);padding:1px 6px;border-radius:6px;font-size:0.92em;font-family:ui-monospace,monospace">$1</code>'
  );

  return safe;
}

export default function Markdown({ text, className = "" }) {
  if (!text) return null;
  const lines = String(text).split("\n");
  const blocks = [];
  let listType = null; // "ul" | "ol" | null
  let listItems = [];
  const flushList = () => {
    if (listItems.length > 0) {
      blocks.push({ type: listType, items: [...listItems] });
      listItems = [];
      listType = null;
    }
  };
  let paragraph = [];
  const flushParagraph = () => {
    if (paragraph.length > 0) {
      blocks.push({ type: "p", text: paragraph.join(" ") });
      paragraph = [];
    }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (line === "") {
      flushList();
      flushParagraph();
      continue;
    }
    const ulMatch = line.match(/^[-•*]\s+(.+)$/);
    const olMatch = line.match(/^(\d+)\.\s+(.+)$/);
    if (ulMatch) {
      flushParagraph();
      if (listType !== "ul") flushList();
      listType = "ul";
      listItems.push(ulMatch[1]);
    } else if (olMatch) {
      flushParagraph();
      if (listType !== "ol") flushList();
      listType = "ol";
      listItems.push(olMatch[2]);
    } else {
      flushList();
      paragraph.push(line);
    }
  }
  flushList();
  flushParagraph();

  return (
    <div className={className}>
      {blocks.map((b, i) => {
        if (b.type === "p") {
          return (
            <p
              key={i}
              className={i > 0 ? "mt-2" : ""}
              dangerouslySetInnerHTML={{ __html: renderInline(b.text) }}
            />
          );
        }
        if (b.type === "ul") {
          return (
            <ul key={i} className="list-disc pl-5 mt-2 space-y-1">
              {b.items.map((it, j) => (
                <li key={j} dangerouslySetInnerHTML={{ __html: renderInline(it) }} />
              ))}
            </ul>
          );
        }
        if (b.type === "ol") {
          return (
            <ol key={i} className="list-decimal pl-5 mt-2 space-y-1">
              {b.items.map((it, j) => (
                <li key={j} dangerouslySetInnerHTML={{ __html: renderInline(it) }} />
              ))}
            </ol>
          );
        }
        return null;
      })}
    </div>
  );
}
