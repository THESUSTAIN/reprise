import { useEffect, useState } from "react";
import api from "@/lib/api";

/**
 * Hook universel pour consommer un contenu WP côté React.
 *
 * Permet à n'importe quelle page React (MyExtension, Tarifs, Contact, FAQ, etc.)
 * de tirer son contenu (titre, sous-titre, paragraphes, meta) directement depuis
 * WordPress, sans nécessiter de redéploiement React quand le contenu change.
 *
 * Le sync est bidirectionnel :
 *   1. L'utilisateur édite la page dans WP-Admin (cms.zayado.net)
 *   2. Le backend FastAPI sert /api/wp/page/{slug} (cache 30 s)
 *   3. Webhook Make ou mu-plugin → cache purgé instantanément (cf. /app/docs/wp-mu-plugin.php)
 *   4. La page React rend le nouveau contenu au prochain refresh
 *
 * Stratégie hybride :
 *   - Si WP renvoie un contenu (exists: true) → on l'utilise (avec yoast meta)
 *   - Sinon → fallback React hardcodé (`fallback`)
 *
 * Usage :
 *   const wp = useWpContent("tarifs", { title: "Tarifs", subtitle: "..." });
 *   <h1>{wp.title}</h1>
 *   <p>{wp.subtitle}</p>
 *   <meta title={wp.seo.title} />
 */
export default function useWpContent(slug, fallback = {}) {
  const [data, setData] = useState({
    loading: true,
    error: null,
    exists: false,
    title: fallback.title || "",
    subtitle: fallback.subtitle || "",
    content_html: fallback.content_html || "",
    excerpt: fallback.excerpt || "",
    modified: null,
    seo: {
      title: fallback.seo?.title || fallback.title || "Zayado",
      description: fallback.seo?.description || fallback.subtitle || "",
      og_image: fallback.seo?.og_image || null,
      canonical: fallback.seo?.canonical || null,
    },
    raw: null,
    ...fallback,
  });

  useEffect(() => {
    let mounted = true;
    api.get(`/wp/page/${slug}`)
      .then(({ data: r }) => {
        if (!mounted) return;
        if (r?.exists) {
          const yoast = r.yoast || {};
          setData((prev) => ({
            ...prev,
            loading: false,
            error: null,
            exists: true,
            title: r.title || prev.title,
            subtitle: r.subtitle || yoast.description || prev.subtitle,
            excerpt: r.excerpt || prev.excerpt,
            content_html: r.content_html || prev.content_html,
            modified: r.modified || null,
            seo: {
              title: yoast.title || r.title || prev.seo.title,
              description: yoast.description || prev.seo.description,
              og_image: yoast.og_image || prev.seo.og_image,
              canonical: yoast.canonical || `https://zayado.net/${slug}`,
            },
            raw: r,
          }));
        } else {
          setData((prev) => ({ ...prev, loading: false, exists: false }));
        }
      })
      .catch((e) => {
        if (!mounted) return;
        setData((prev) => ({ ...prev, loading: false, error: e?.message || "WP fetch failed" }));
      });
    return () => { mounted = false; };
  }, [slug]);

  return data;
}
