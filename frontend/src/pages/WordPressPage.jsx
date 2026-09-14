/* WordPressPage — composant générique qui rend n'importe quelle page WP
 * publiée sur cms.zayado.net dans le site React.
 *
 * Usage :
 *   <Route path="/wp/:slug" element={<WordPressPage />} />
 *
 * Fonctionnement :
 *   1. Récupère le slug depuis l'URL
 *   2. Fetch /api/wp/page/:slug (backend, cache 30 s)
 *   3. Si exists=true → rend le HTML Gutenberg dans un wrapper Helmet (SEO)
 *   4. Si exists=false → 404 friendly
 *   5. Si erreur API → message + retry
 */
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Loader2, RefreshCw, ArrowLeft } from "lucide-react";
import api from "@/lib/api";
import { PublicHeader, UnifiedFooter } from "@/pages/LandingHub";

export default function WordPressPage() {
  const { slug } = useParams();
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    api.get(`/wp/page/${slug}`)
      .then(({ data }) => setPage(data))
      .catch((e) => setError(e?.response?.data?.detail || "Page WordPress indisponible"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [slug]);

  const yoast = page?.yoast || {};
  const title = yoast.title || page?.title || `Zayado · ${slug}`;
  const description = yoast.description || "Page Zayado synchronisée depuis WordPress.";

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }}>
      <Helmet>
        <title>{title}</title>
        <meta name="description" content={description} />
        {yoast.canonical && <link rel="canonical" href={yoast.canonical} />}
        {yoast.og_image && <meta property="og:image" content={yoast.og_image} />}
      </Helmet>

      <PublicHeader />

      <main className="flex-1 max-w-4xl mx-auto px-6 py-16" data-testid={`wp-page-${slug}`}>
        {loading && (
          <div className="text-center py-24 flex flex-col items-center gap-3">
            <Loader2 className="animate-spin" size={28} style={{ color: "var(--zayado-navy)" }} />
            <p className="text-[13px]" style={{ color: "#6b7280" }}>Chargement depuis WordPress…</p>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-3xl p-10 text-center shadow-md bg-white" data-testid="wp-page-error">
            <h2 className="font-display text-2xl mb-2" style={{ color: "var(--zayado-navy)" }}>Impossible de charger la page</h2>
            <p className="text-[13.5px] mb-5" style={{ color: "#6b7280" }}>{error}</p>
            <button onClick={load} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-[13px] font-semibold shadow-md"
                    style={{ background: "var(--zayado-navy)", color: "#f6f3ee" }}>
              <RefreshCw size={13} /> Réessayer
            </button>
          </div>
        )}

        {!loading && !error && page && !page.exists && (
          <div className="rounded-3xl p-10 text-center shadow-md bg-white" data-testid="wp-page-not-found">
            <h2 className="font-display text-3xl mb-2" style={{ color: "var(--zayado-navy)" }}>Page introuvable</h2>
            <p className="text-[14px] mb-5" style={{ color: "#6b7280" }}>
              La page <code className="px-2 py-0.5 rounded" style={{ background: "var(--zayado-cream-dark)" }}>/{slug}</code> n&apos;existe pas (encore) sur WordPress.
            </p>
            <Link to="/" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-[13px] font-semibold shadow-md"
                  style={{ background: "var(--zayado-navy)", color: "#f6f3ee" }}>
              <ArrowLeft size={13} /> Retour à l&apos;accueil
            </Link>
          </div>
        )}

        {!loading && !error && page?.exists && (
          <article className="bg-white rounded-3xl p-8 sm:p-12 shadow-md" data-testid="wp-page-content">
            <h1
              className="font-display text-[40px] sm:text-[52px] leading-[1.05] mb-8"
              style={{ color: "var(--zayado-text)", letterSpacing: "-0.025em" }}
              dangerouslySetInnerHTML={{ __html: page.title }}
            />
            <div
              className="wp-content prose-zayado"
              dangerouslySetInnerHTML={{ __html: page.content_html }}
            />
            <div className="mt-10 pt-6 border-t border-[var(--zayado-border)] text-[12px]" style={{ color: "#6b7280" }}>
              Dernière mise à jour WordPress : {page.modified ? new Date(page.modified).toLocaleString("fr-FR") : "—"}
            </div>
          </article>
        )}
      </main>

      <UnifiedFooter />
    </div>
  );
}
