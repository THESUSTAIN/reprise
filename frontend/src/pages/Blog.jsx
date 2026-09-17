/* Blog public Zayado — `/blog` (liste) et `/blog/:slug` (détail).

   Affiche les articles publiés sur WordPress via /api/blog/posts.
   Si WP non configuré ou catalogue vide → fallback mock (géré côté backend).

   Design éditorial : hero magazine, grille de cards, page article serif italique. */
import React, { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Calendar, Clock, ArrowLeft, Loader2, BookOpen } from "lucide-react";
import api, { SAAS_URL } from "@/lib/api";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
  } catch { return ""; }
}

function readingTime(html) {
  if (!html) return 3;
  const words = html.replace(/<[^>]+>/g, " ").split(/\s+/).length;
  return Math.max(2, Math.round(words / 220));
}

// ── Liste articles ────────────────────────────────────────────────────────
function BlogList() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/blog/posts", { params: { per_page: 24 } })
      .then((r) => setPosts(r.data?.posts || []))
      .finally(() => setLoading(false));
  }, []);

  const featured = posts[0];
  const rest = posts.slice(1);

  return (
    <div className="min-h-screen" style={{ background: "var(--zayado-cream)" }} data-testid="blog-list-page">
      <Helmet>
        <title>Le journal Zayado · Conseils pour entrepreneurs apaisés</title>
        <meta name="description" content="Articles, guides et conseils pour les entrepreneurs solos : création d'entreprise, mutuelle TNS, énergie, pilotage financier." />
      </Helmet>

      {/* Hero */}
      <section className="max-w-[1200px] mx-auto px-4 md:px-6 pt-12 pb-10">
        <div className="text-[11px] uppercase tracking-[0.25em] mb-3" style={{ color: GOLD }}>
          Le Journal Zayado
        </div>
        <h1 className="font-display italic mb-3"
            style={{ fontFamily: "'DM Serif Display', serif",
                     fontSize: "clamp(2.2rem, 5vw, 3.8rem)", lineHeight: 1.05, color: NAVY }}>
          Entreprendre, <em>autrement.</em>
        </h1>
        <p className="text-base max-w-xl leading-relaxed" style={{ color: MUTED }}>
          Articles, guides et conseils pratiques pour fondateurs solos. Sans bullshit motivationnel, sans hacks miraculeux.
        </p>
      </section>

      {loading && (
        <div className="flex items-center gap-2 text-sm py-16 justify-center" style={{ color: MUTED }}>
          <Loader2 size={16} className="animate-spin" /> Chargement…
        </div>
      )}

      {!loading && posts.length === 0 && (
        <div className="max-w-[600px] mx-auto px-4 py-16 text-center" data-testid="blog-empty">
          <BookOpen size={32} className="mx-auto mb-3" style={{ color: GOLD }} />
          <h3 className="font-bold text-lg mb-2" style={{ color: NAVY }}>Premiers articles bientôt en ligne</h3>
          <p className="text-sm" style={{ color: MUTED }}>
            Nos articles seront publiés depuis la rédaction Zayado.
          </p>
        </div>
      )}

      {!loading && featured && (
        <section className="max-w-[1200px] mx-auto px-4 md:px-6 pb-10" data-testid="blog-featured">
          <Link to={`/blog/${featured.slug}`} className="block group">
            <div className="grid md:grid-cols-2 gap-8 bg-white border border-[var(--zayado-border)] rounded-3xl overflow-hidden hover:shadow-xl transition-shadow">
              <div className="aspect-[4/3] md:aspect-auto overflow-hidden">
                {featured.featured_image ? (
                  <img src={featured.featured_image} alt={featured.title}
                       className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                ) : (
                  <div className="w-full h-full" style={{ background: "var(--zayado-cream)" }} />
                )}
              </div>
              <div className="p-8 md:p-10 flex flex-col justify-center">
                <div className="text-[11px] uppercase tracking-[0.25em] mb-3" style={{ color: GOLD }}>
                  À la une · {featured.categories?.[0] || "Article"}
                </div>
                <h2 className="font-display italic mb-3"
                    style={{ fontFamily: "'DM Serif Display', serif",
                             fontSize: "clamp(1.5rem, 3vw, 2.4rem)", lineHeight: 1.15, color: NAVY }}
                    dangerouslySetInnerHTML={{ __html: featured.title }} />
                <div className="text-sm leading-relaxed mb-4" style={{ color: MUTED }}
                     dangerouslySetInnerHTML={{ __html: featured.excerpt }} />
                <div className="text-xs flex items-center gap-4" style={{ color: MUTED }}>
                  <span className="inline-flex items-center gap-1.5"><Calendar size={11} /> {formatDate(featured.date)}</span>
                  <span className="inline-flex items-center gap-1.5"><Clock size={11} /> {readingTime(featured.content_html || featured.excerpt)} min</span>
                </div>
              </div>
            </div>
          </Link>
        </section>
      )}

      {!loading && rest.length > 0 && (
        <section className="max-w-[1200px] mx-auto px-4 md:px-6 pb-20" data-testid="blog-grid">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-7">
            {rest.map((p) => (
              <Link key={p.id || p.slug} to={`/blog/${p.slug}`}
                    className="block group bg-white border border-[var(--zayado-border)] rounded-2xl overflow-hidden hover:border-[var(--zayado-navy)] transition-colors"
                    data-testid={`blog-card-${p.slug}`}>
                {p.featured_image ? (
                  <div className="aspect-[4/3] overflow-hidden">
                    <img src={p.featured_image} alt={p.title}
                         className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                  </div>
                ) : (
                  <div className="aspect-[4/3]" style={{ background: "var(--zayado-cream)" }} />
                )}
                <div className="p-5">
                  <div className="text-[10px] uppercase tracking-[0.2em] mb-2" style={{ color: GOLD }}>
                    {p.categories?.[0] || "Article"}
                  </div>
                  <h3 className="font-bold text-base leading-snug mb-2" style={{ color: NAVY }}
                      dangerouslySetInnerHTML={{ __html: p.title }} />
                  <div className="text-xs leading-relaxed mb-3 line-clamp-2" style={{ color: MUTED }}
                       dangerouslySetInnerHTML={{ __html: p.excerpt }} />
                  <div className="text-[11px] flex items-center gap-3" style={{ color: MUTED }}>
                    <span>{formatDate(p.date)}</span>
                    <span>·</span>
                    <span>{readingTime(p.content_html || p.excerpt)} min</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// ── Détail article ────────────────────────────────────────────────────────
function BlogPost() {
  const { slug } = useParams();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.get(`/blog/posts/${slug}`)
      .then((r) => setPost(r.data))
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center" style={{ background: "var(--zayado-cream)" }}>
        <Loader2 size={20} className="animate-spin" style={{ color: NAVY }} />
      </div>
    );
  }

  if (notFound || !post) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center px-4 text-center" style={{ background: "var(--zayado-cream)" }}>
        <BookOpen size={28} className="mb-3" style={{ color: GOLD }} />
        <h2 className="font-bold text-lg mb-2" style={{ color: NAVY }}>Article introuvable</h2>
        <Link to="/blog" className="text-sm hover:underline" style={{ color: NAVY }}>← Retour au journal</Link>
      </div>
    );
  }

  return (
    <article className="min-h-screen" style={{ background: "var(--zayado-cream)" }} data-testid="blog-post-page">
      <Helmet>
        <title>{`${(post.title || "").replace(/<[^>]+>/g, "")} · Journal Zayado`}</title>
        <meta name="description" content={(post.excerpt || "").replace(/<[^>]+>/g, "").slice(0, 160)} />
      </Helmet>

      <div className="max-w-[760px] mx-auto px-4 md:px-6 pt-10 pb-16">
        <Link to="/blog" className="text-xs hover:underline inline-flex items-center gap-1 mb-7" style={{ color: MUTED }}>
          <ArrowLeft size={11} /> Le journal
        </Link>

        <div className="text-[11px] uppercase tracking-[0.25em] mb-3" style={{ color: GOLD }}>
          {post.categories?.[0] || "Article"}
        </div>

        <h1 className="font-display italic mb-5"
            style={{ fontFamily: "'DM Serif Display', serif",
                     fontSize: "clamp(2rem, 4.5vw, 3.4rem)", lineHeight: 1.1, color: NAVY }}
            dangerouslySetInnerHTML={{ __html: post.title }}
            data-testid="blog-post-title" />

        <div className="flex items-center gap-4 text-xs mb-8 pb-6 border-b border-[var(--zayado-border)]" style={{ color: MUTED }}>
          <span className="inline-flex items-center gap-1.5"><Calendar size={11} /> {formatDate(post.date)}</span>
          <span className="inline-flex items-center gap-1.5"><Clock size={11} /> {readingTime(post.content_html)} min de lecture</span>
          <span>par {post.author}</span>
        </div>

        {post.featured_image && (
          <div className="aspect-[16/9] rounded-2xl overflow-hidden mb-8">
            <img src={post.featured_image} alt={post.title} className="w-full h-full object-cover" />
          </div>
        )}

        <div
          className="prose prose-lg max-w-none text-[var(--zayado-text)] leading-relaxed
                     prose-headings:font-display prose-headings:italic prose-headings:text-[var(--zayado-navy)]
                     prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-3
                     prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-2
                     prose-p:text-base prose-p:leading-relaxed
                     prose-a:text-[var(--zayado-navy)] prose-a:underline
                     prose-strong:text-[var(--zayado-navy)]
                     prose-img:rounded-xl prose-img:my-6
                     prose-ul:my-4 prose-li:my-1"
          dangerouslySetInnerHTML={{ __html: post.content_html }}
          data-testid="blog-post-content"
        />

        <div className="mt-12 pt-8 border-t border-[var(--zayado-border)] flex flex-wrap items-center justify-between gap-4">
          <Link to="/blog"
                className="inline-flex items-center gap-2 text-sm hover:underline"
                style={{ color: NAVY }}>
            ← Lire les autres articles
          </Link>
          <a href={SAAS_URL + "/login"}
             className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-white text-sm font-medium"
             style={{ background: NAVY }}
             data-testid="article-cta-login">
            Essayer Zayado gratuitement →
          </a>
        </div>
      </div>
    </article>
  );
}

export default function Blog() {
  const loc = useLocation();
  if (loc.pathname.startsWith("/blog/") && loc.pathname.length > 6) return <BlogPost />;
  return <BlogList />;
}
