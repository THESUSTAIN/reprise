/**
 * Hybrid WP content renderer — slot-based.
 *
 * Convention :  the WP page is structured with "📍 <Section name>" H2 markers,
 * followed by content blocks. We split the content into named sections and
 * each React page picks the slot it needs.
 *
 * Within a section we also expose :
 *   - heading (first H1/H2/H3 after the 📍 marker, NOT the marker itself)
 *   - subtitle (first <p> after the heading)
 *   - paragraphs[]  (all subsequent <p> blocks, raw HTML)
 *   - extras{key:value}  parsed from "<strong>Key:</strong> value" patterns
 */
import React, { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import api from "@/lib/api";

const slugify = (s) =>
  (s || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/^📍\s*/, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

export function useWPPage(slug) {
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(() => {
    let cancel = false;
    setLoading(true);
    // Try the new WP-direct endpoint first, fall back to legacy /public/pages
    api.get(`/wp/page/${slug}`)
      .then((r) => {
        if (cancel) return;
        const d = r.data || {};
        if (d.exists) {
          // Adapt new shape → legacy shape used by parseWPContent
          setPage({
            slug: d.slug,
            title: { rendered: d.title || "" },
            content: { rendered: d.content_html || "" },
            excerpt: { rendered: d.excerpt_html || "" },
            yoast: d.yoast,
          });
        } else {
          setPage(null);
        }
      })
      .catch(() => {
        // Fallback to legacy endpoint
        api.get(`/public/pages/${slug}`)
          .then((r) => { if (!cancel) setPage(r.data); })
          .catch((e) => { if (!cancel) setError(e?.response?.data?.detail || e.message); });
      })
      .finally(() => { if (!cancel) setLoading(false); });
    return () => { cancel = true; };
  }, [slug]);
  return { page, loading, error };
}

/**
 * Pull WooCommerce products from WP (via /api/wp/products).
 */
export function useWPProducts({ perPage = 24, page = 1, category = "" } = {}) {
  const [data, setData] = useState({ items: [], total: 0, total_pages: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(() => {
    let cancel = false;
    setLoading(true);
    api.get(`/wp/products`, { params: { per_page: perPage, page, category } })
      .then((r) => { if (!cancel) setData(r.data || { items: [] }); })
      .catch((e) => { if (!cancel) setError(e?.response?.data?.detail || e.message); })
      .finally(() => { if (!cancel) setLoading(false); });
    return () => { cancel = true; };
  }, [perPage, page, category]);
  return { ...data, loading, error };
}

/**
 * Pull single WooCommerce product by slug.
 */
export function useWPProduct(slug) {
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(() => {
    if (!slug) return;
    let cancel = false;
    setLoading(true);
    api.get(`/wp/product/${slug}`)
      .then((r) => { if (!cancel) setProduct(r.data); })
      .catch((e) => { if (!cancel) setError(e?.response?.data?.detail || e.message); })
      .finally(() => { if (!cancel) setLoading(false); });
    return () => { cancel = true; };
  }, [slug]);
  return { product, loading, error };
}

/**
 * Parse Gutenberg-rendered HTML into named sections.
 * Returns: { sections: { <slug>: SectionData }, ordered: [<slug>...] }
 */
export function parseWPContent(html) {
  const empty = { sections: {}, ordered: [], title: "", subtitle: "" };
  if (!html) return empty;
  const root = document.createElement("div");
  root.innerHTML = html;
  const nodes = Array.from(root.children);

  const sections = {};
  const ordered = [];
  let current = null;
  let pageTitle = "";
  let pageSubtitle = "";

  const ensureSection = (name) => {
    const slug = slugify(name) || "default";
    if (!sections[slug]) {
      sections[slug] = { name: name.replace(/^📍\s*/, "").trim(), heading: "", subtitle: "", paragraphs: [], extras: {} };
      ordered.push(slug);
    }
    return sections[slug];
  };

  // First pass: split by 📍 markers (H2 with 📍 prefix).
  for (const n of nodes) {
    const tag = n.tagName?.toLowerCase();
    const html = n.outerHTML;
    const text = n.textContent.trim();
    if (!text) continue;

    const isMarker = tag === "h2" && text.startsWith("📍");
    if (isMarker) {
      current = ensureSection(text);
      continue;
    }
    if (!current) {
      // before any marker → treat as page-level intro
      if (tag === "h1" && !pageTitle) { pageTitle = n.innerHTML; continue; }
      if (tag === "p" && pageTitle && !pageSubtitle) { pageSubtitle = n.innerHTML; continue; }
      current = ensureSection("default");
    }

    if (["h1", "h2", "h3"].includes(tag) && !current.heading) {
      current.heading = n.innerHTML;
    } else if (tag === "p") {
      // Extract "<strong>Key:</strong> Value" patterns into extras
      const m = n.innerHTML.match(/^<strong>([^<:]+)\s*:?<\/strong>\s*(.*)$/i);
      if (m) {
        current.extras[slugify(m[1])] = m[2].trim();
      } else if (!current.subtitle) {
        current.subtitle = n.innerHTML;
      } else {
        current.paragraphs.push(n.innerHTML);
      }
    } else {
      current.paragraphs.push(html);
    }
  }

  return { sections, ordered, title: pageTitle, subtitle: pageSubtitle };
}

/** Helper: get a section by anchor slug with safe defaults. */
export const getSection = (parsed, anchor, fallback = {}) => {
  const s = parsed?.sections?.[anchor];
  return {
    name: s?.name || fallback.name || anchor,
    heading: s?.heading || fallback.heading || "",
    subtitle: s?.subtitle || fallback.subtitle || "",
    paragraphs: s?.paragraphs || fallback.paragraphs || [],
    extras: s?.extras || fallback.extras || {},
  };
};

export function WPLoading() {
  return (
    <div className="py-24 text-center text-ink-soft">
      <Loader2 className="inline animate-spin mr-2" /> Chargement…
    </div>
  );
}
