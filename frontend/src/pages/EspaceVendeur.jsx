/* Espace vendeur — dépôt de produits pour la marketplace Zayado.
 *
 * Fond blanc volontaire, hors du cockpit sombre. Ce n'est pas une préférence
 * esthétique : un vendeur qui remplit une fiche produit regarde des photos et
 * juge des couleurs. Sur fond sombre, il évalue mal ses propres images.
 *
 * Le parcours suit l'ordre des questions que se pose un vendeur :
 *   qui suis-je (profil) → qu'est-ce que je vends (fiche) → où en est-ce (statut)
 *
 * Le statut d'un produit n'est jamais un simple badge : chaque état dit ce
 * qu'il attend du vendeur, et un refus affiche toujours son motif.
 */
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Store, Plus, Loader2, Check, X, Clock, AlertCircle, Trash2, Pencil,
  Image as ImageIcon, ExternalLink, ArrowLeft, Info, Send,
} from "lucide-react";
import { toast } from "sonner";
import {
  getVendeurEtat, saveVendeurProfil, getVendeurProduits, createVendeurProduit,
  updateVendeurProduit, deleteVendeurProduit, submitVendeurProduit, checkVendeurProduit,
} from "../lib/api";

/* Palette claire, isolée du thème sombre du cockpit. */
const C = {
  encre: "#111827", texte: "#374151", doux: "#6B7280", tres_doux: "#9CA3AF",
  bord: "#E5E7EB", fond: "#FFFFFF", fond2: "#F9FAFB", navy: "#0B1B3A",
};

const STATUTS = {
  brouillon: { label: "Brouillon", couleur: "#6B7280", fond: "#F3F4F6", Icone: Pencil,
    aide: "Visible de vous seul. Complétez la fiche puis envoyez-la à la vérification." },
  en_attente: { label: "En vérification", couleur: "#B45309", fond: "#FEF3C7", Icone: Clock,
    aide: "Zayado relit votre fiche. Elle n'est plus modifiable jusqu'à la réponse." },
  publie: { label: "En ligne", couleur: "#047857", fond: "#D1FAE5", Icone: Check,
    aide: "Le produit existe dans la boutique. Toute modification repasse par une vérification." },
  refuse: { label: "À corriger", couleur: "#B91C1C", fond: "#FEE2E2", Icone: AlertCircle,
    aide: "Corrigez ce qui est indiqué, la fiche repassera en brouillon." },
};

const VIDE = { titre: "", description: "", prix: "", stock: "", sku: "", categorie: "", images: [] };

function Etiquette({ children, obligatoire, aide }) {
  return (
    <div className="mb-1.5">
      <span className="text-[13px] font-semibold" style={{ color: C.encre }}>
        {children}{obligatoire && <span style={{ color: "#DC2626" }}> *</span>}
      </span>
      {aide && <span className="mt-0.5 block text-[12px] leading-snug" style={{ color: C.doux }}>{aide}</span>}
    </div>
  );
}

const saisie = {
  width: "100%", borderRadius: 10, border: `1px solid ${C.bord}`, background: C.fond,
  padding: "9px 12px", fontSize: 14, color: C.encre, outline: "none",
};

/* ── Formulaire d'une fiche ──────────────────────────────────── */
function Formulaire({ initial, onAnnuler, onEnregistrer, enregistrement }) {
  const [f, setF] = useState({ ...VIDE, ...initial, images: initial?.images || [] });
  const [nouvelleImage, setNouvelleImage] = useState("");
  const maj = (k, v) => setF((p) => ({ ...p, [k]: v }));

  const ajouterImage = () => {
    const url = nouvelleImage.trim();
    if (!url) return;
    if (!/^https?:\/\//.test(url)) {
      toast.error("L'adresse doit commencer par https://");
      return;
    }
    if (f.images.length >= 6) {
      toast.error("6 images maximum.");
      return;
    }
    maj("images", [...f.images, url]);
    setNouvelleImage("");
  };

  const caracteres = (f.description || "").replace(/<[^>]+>/g, "").trim().length;

  return (
    <div style={{ background: C.fond, border: `1px solid ${C.bord}`, borderRadius: 16, padding: 24 }}>
      <h2 className="m-0 text-[17px] font-semibold" style={{ color: C.encre }}>
        {initial?.id ? "Modifier la fiche" : "Nouveau produit"}
      </h2>
      <p className="m-0 mt-1 text-[13px] leading-relaxed" style={{ color: C.doux }}>
        Ces informations partiront telles quelles dans la boutique. Écrivez-les comme si vous parliez
        à quelqu'un qui hésite.
      </p>

      <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <Etiquette obligatoire>Nom du produit</Etiquette>
          <input style={saisie} data-testid="produit-titre" value={f.titre}
            onChange={(e) => maj("titre", e.target.value)}
            placeholder="Ex : Savon solide au lait d'ânesse — 100 g" />
        </div>

        <div className="md:col-span-2">
          <Etiquette obligatoire aide="30 caractères minimum. Dites la matière, la taille, l'usage — c'est ce qui décide l'achat.">
            Description
          </Etiquette>
          <textarea style={{ ...saisie, minHeight: 120, resize: "vertical", fontFamily: "inherit" }}
            data-testid="produit-description" value={f.description}
            onChange={(e) => maj("description", e.target.value)}
            placeholder="Fabriqué à la main dans le Morbihan, sans huile de palme…" />
          <p className="m-0 mt-1 text-[11.5px]" style={{ color: caracteres < 30 ? "#B45309" : C.tres_doux }}>
            {caracteres} caractère{caracteres > 1 ? "s" : ""}{caracteres < 30 ? ` — encore ${30 - caracteres}` : ""}
          </p>
        </div>

        <div>
          <Etiquette obligatoire>Prix TTC (€)</Etiquette>
          <input style={saisie} data-testid="produit-prix" value={f.prix} inputMode="decimal"
            onChange={(e) => maj("prix", e.target.value)} placeholder="12,90" />
        </div>
        <div>
          <Etiquette aide="Laissez vide si vous ne suivez pas le stock.">Stock</Etiquette>
          <input style={saisie} data-testid="produit-stock" value={f.stock ?? ""} inputMode="numeric"
            onChange={(e) => maj("stock", e.target.value)} placeholder="25" />
        </div>
        <div>
          <Etiquette aide="Votre référence interne, facultative.">Référence (SKU)</Etiquette>
          <input style={saisie} value={f.sku || ""} onChange={(e) => maj("sku", e.target.value)} placeholder="SAV-ANE-100" />
        </div>
        <div>
          <Etiquette>Catégorie</Etiquette>
          <input style={saisie} value={f.categorie || ""} onChange={(e) => maj("categorie", e.target.value)} placeholder="Soin & bien-être" />
        </div>

        <div className="md:col-span-2">
          <Etiquette obligatoire aide="Adresse web de vos photos, 6 maximum. La première sera l'image principale.">
            Images
          </Etiquette>
          <div className="flex gap-2">
            <input style={saisie} data-testid="produit-image-url" value={nouvelleImage}
              onChange={(e) => setNouvelleImage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), ajouterImage())}
              placeholder="https://…/mon-produit.jpg" />
            <button type="button" onClick={ajouterImage} data-testid="produit-ajouter-image"
              style={{ borderRadius: 10, border: `1px solid ${C.bord}`, background: C.fond2,
                       padding: "9px 16px", fontSize: 13, fontWeight: 600, color: C.encre, whiteSpace: "nowrap" }}>
              Ajouter
            </button>
          </div>
          {f.images.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {f.images.map((url, i) => (
                <div key={url} style={{ position: "relative", width: 88, height: 88, borderRadius: 10,
                                        overflow: "hidden", border: `1px solid ${C.bord}`, background: C.fond2 }}>
                  <img src={url} alt={`Visuel ${i + 1}`} style={{ width: "100%", height: "100%", objectFit: "cover" }}
                    onError={(e) => { e.currentTarget.style.display = "none"; }} />
                  <button type="button" onClick={() => maj("images", f.images.filter((u) => u !== url))}
                    aria-label={`Retirer l'image ${i + 1}`}
                    style={{ position: "absolute", top: 4, right: 4, width: 20, height: 20, borderRadius: 999,
                             border: "none", background: "rgba(17,24,39,.75)", color: "#fff", cursor: "pointer",
                             display: "grid", placeItems: "center" }}>
                    <X size={11} />
                  </button>
                  {i === 0 && (
                    <span style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "rgba(17,24,39,.75)",
                                   color: "#fff", fontSize: 9, textAlign: "center", padding: "2px 0" }}>principale</span>
                  )}
                </div>
              ))}
            </div>
          )}
          {f.images.length === 0 && (
            <div className="mt-2 flex items-center gap-2 rounded-xl px-3 py-4"
              style={{ border: `1px dashed ${C.bord}`, color: C.tres_doux }}>
              <ImageIcon size={15} /> <span className="text-[12.5px]">Aucune image pour l'instant.</span>
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <button onClick={() => onEnregistrer(f)} disabled={enregistrement} data-testid="produit-enregistrer"
          style={{ borderRadius: 999, border: "none", background: C.navy, color: "#fff",
                   padding: "10px 22px", fontSize: 14, fontWeight: 600, cursor: "pointer", opacity: enregistrement ? .6 : 1 }}>
          {enregistrement ? "Enregistrement…" : "Enregistrer le brouillon"}
        </button>
        <button onClick={onAnnuler}
          style={{ borderRadius: 999, border: `1px solid ${C.bord}`, background: C.fond,
                   padding: "10px 22px", fontSize: 14, fontWeight: 600, color: C.texte, cursor: "pointer" }}>
          Annuler
        </button>
      </div>
    </div>
  );
}

/* ── Une ligne produit ───────────────────────────────────────── */
function LigneProduit({ produit, onModifier, onSupprimer, onSoumettre, occupe }) {
  const s = STATUTS[produit.statut] || STATUTS.brouillon;
  const { Icone } = s;
  const modifiable = produit.statut !== "en_attente";

  return (
    <article data-testid={`produit-${produit.id}`}
      style={{ display: "flex", gap: 16, alignItems: "flex-start", background: C.fond,
               border: `1px solid ${C.bord}`, borderRadius: 14, padding: 16 }}>
      <div style={{ width: 68, height: 68, borderRadius: 10, overflow: "hidden", flexShrink: 0,
                    background: C.fond2, display: "grid", placeItems: "center" }}>
        {produit.images?.[0]
          ? <img src={produit.images[0]} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }}
              onError={(e) => { e.currentTarget.style.display = "none"; }} />
          : <ImageIcon size={20} color={C.tres_doux} />}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="flex flex-wrap items-center gap-2">
          <p className="m-0 truncate text-[14.5px] font-semibold" style={{ color: C.encre }}>
            {produit.titre || "Produit sans nom"}
          </p>
          <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold"
            style={{ background: s.fond, color: s.couleur }}>
            <Icone size={10} /> {s.label}
          </span>
        </div>
        <p className="m-0 mt-1 text-[12.5px]" style={{ color: C.doux }}>
          {produit.prix ? `${String(produit.prix).replace(".", ",")} €` : "Prix à définir"}
          {produit.stock !== "" && produit.stock != null ? ` · ${produit.stock} en stock` : ""}
          {produit.categorie ? ` · ${produit.categorie}` : ""}
        </p>
        <p className="m-0 mt-1.5 text-[12px] leading-relaxed" style={{ color: C.tres_doux }}>{s.aide}</p>

        {produit.statut === "refuse" && produit.motif_refus && (
          <p className="m-0 mt-2 rounded-lg px-3 py-2 text-[12.5px] leading-relaxed"
            style={{ background: "#FEF2F2", color: "#991B1B" }}>
            <strong>Motif : </strong>{produit.motif_refus}
          </p>
        )}

        <div className="mt-3 flex flex-wrap gap-2">
          {modifiable && (
            <button onClick={() => onModifier(produit)} data-testid={`modifier-${produit.id}`}
              style={{ display: "inline-flex", alignItems: "center", gap: 5, borderRadius: 999,
                       border: `1px solid ${C.bord}`, background: C.fond, padding: "6px 14px",
                       fontSize: 12.5, fontWeight: 600, color: C.texte, cursor: "pointer" }}>
              <Pencil size={12} /> Modifier
            </button>
          )}
          {(produit.statut === "brouillon") && (
            <button onClick={() => onSoumettre(produit)} disabled={occupe} data-testid={`soumettre-${produit.id}`}
              style={{ display: "inline-flex", alignItems: "center", gap: 5, borderRadius: 999, border: "none",
                       background: C.navy, color: "#fff", padding: "6px 14px", fontSize: 12.5,
                       fontWeight: 600, cursor: "pointer", opacity: occupe ? .6 : 1 }}>
              <Send size={12} /> Envoyer à la vérification
            </button>
          )}
          {produit.statut === "publie" && produit.shopify_handle && (
            <span className="inline-flex items-center gap-1 text-[12.5px] font-semibold" style={{ color: "#047857" }}>
              <ExternalLink size={12} /> {produit.shopify_handle}
            </span>
          )}
          {modifiable && (
            <button onClick={() => onSupprimer(produit)} aria-label="Supprimer"
              style={{ display: "inline-flex", alignItems: "center", gap: 5, borderRadius: 999,
                       border: "none", background: "transparent", padding: "6px 8px",
                       fontSize: 12.5, color: C.tres_doux, cursor: "pointer" }}>
              <Trash2 size={13} />
            </button>
          )}
        </div>
      </div>
    </article>
  );
}

/* ── Écran ───────────────────────────────────────────────────── */
export default function EspaceVendeur() {
  const navigate = useNavigate();
  const [etat, setEtat] = useState(null);
  const [produits, setProduits] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [profil, setProfil] = useState(null);
  const [editionProfil, setEditionProfil] = useState(false);
  const [edition, setEdition] = useState(null);   // null | {} | produit
  const [occupe, setOccupe] = useState(false);

  const charger = useCallback(async () => {
    setErreur("");
    try {
      const [e, liste] = await Promise.all([getVendeurEtat(), getVendeurProduits()]);
      setEtat(e);
      setProfil(e.profil);
      setProduits(liste?.items || []);
      setEditionProfil(!e.profil_complet);
    } catch {
      setErreur("Impossible de charger votre espace vendeur. Vérifiez votre connexion, puis réessayez.");
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => { charger(); }, [charger]);

  const enregistrerProfil = async () => {
    setOccupe(true);
    try {
      await saveVendeurProfil(profil);
      await charger();
      setEditionProfil(false);
      toast.success("Profil vendeur enregistré.");
    } catch {
      toast.error("Enregistrement impossible pour l'instant.");
    } finally {
      setOccupe(false);
    }
  };

  const enregistrerProduit = async (fiche) => {
    setOccupe(true);
    try {
      if (fiche.id) await updateVendeurProduit(fiche.id, fiche);
      else await createVendeurProduit(fiche);
      setEdition(null);
      await charger();
      toast.success("Fiche enregistrée en brouillon.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Enregistrement impossible.");
    } finally {
      setOccupe(false);
    }
  };

  const soumettre = async (produit) => {
    setOccupe(true);
    try {
      // On vérifie avant d'envoyer : le vendeur voit tout ce qui manque d'un
      // coup, plutôt qu'une erreur à la fois.
      const controle = await checkVendeurProduit(produit.id);
      if (!controle.pret) {
        toast.error(controle.erreurs[0]);
        setEdition(produit);
        return;
      }
      await submitVendeurProduit(produit.id);
      await charger();
      toast.success("Fiche envoyée. Zayado la relit avant mise en ligne.");
    } catch (e) {
      const d = e?.response?.data?.detail;
      toast.error(typeof d === "string" ? d : d?.erreurs?.[0] || "Envoi impossible.");
    } finally {
      setOccupe(false);
    }
  };

  const supprimer = async (produit) => {
    if (!window.confirm(`Supprimer définitivement « ${produit.titre || "ce produit"} » ?`)) return;
    try {
      await deleteVendeurProduit(produit.id);
      await charger();
    } catch {
      toast.error("Suppression impossible.");
    }
  };

  const enveloppe = (contenu) => (
    <div style={{ minHeight: "100vh", background: C.fond2, color: C.encre,
                  fontFamily: "Inter, system-ui, sans-serif" }}>
      <header style={{ background: C.fond, borderBottom: `1px solid ${C.bord}` }}>
        <div style={{ maxWidth: 1080, margin: "0 auto", padding: "14px 20px",
                      display: "flex", alignItems: "center", gap: 12 }}>
          <button onClick={() => navigate("/")} aria-label="Retour au cockpit"
            style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "none",
                     border: "none", color: C.doux, fontSize: 13, cursor: "pointer", padding: 0 }}>
            <ArrowLeft size={15} /> Cockpit
          </button>
          <span style={{ width: 1, height: 18, background: C.bord }} />
          <Store size={17} color={C.navy} />
          <strong style={{ fontSize: 15 }}>Espace vendeur</strong>
        </div>
      </header>
      <main style={{ maxWidth: 1080, margin: "0 auto", padding: "28px 20px 64px" }}>{contenu}</main>
    </div>
  );

  if (chargement) {
    return enveloppe(
      <p className="flex items-center gap-2 text-[14px]" style={{ color: C.doux }}>
        <Loader2 size={16} className="animate-spin" /> Chargement de votre espace…
      </p>
    );
  }

  if (erreur) {
    return enveloppe(
      <div style={{ background: C.fond, border: `1px solid ${C.bord}`, borderRadius: 14, padding: 24 }}>
        <p className="m-0 text-[14px]" style={{ color: C.texte }}>{erreur}</p>
        <button onClick={charger} style={{ marginTop: 12, borderRadius: 999, border: `1px solid ${C.bord}`,
          background: C.fond, padding: "8px 18px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
          Réessayer
        </button>
      </div>
    );
  }

  const c = etat?.compteurs || {};

  return enveloppe(
    <div className="space-y-5">
      <div>
        <h1 className="m-0 text-[26px] font-semibold" style={{ color: C.encre }}>Vos produits sur Zayado</h1>
        <p className="m-0 mt-1.5 max-w-2xl text-[14px] leading-relaxed" style={{ color: C.doux }}>
          Déposez une fiche, envoyez-la à la vérification, Zayado la met en ligne dans la boutique.
          Vous gardez la main sur vos prix et vos textes à tout moment.
        </p>
      </div>

      {/* Compteurs — seulement s'il y a quelque chose à compter. */}
      {produits.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(STATUTS).map(([cle, s]) => (
            <span key={cle} className="rounded-full px-3 py-1 text-[12.5px] font-semibold"
              style={{ background: s.fond, color: s.couleur }}>
              {c[cle] || 0} {s.label.toLowerCase()}
            </span>
          ))}
        </div>
      )}

      {/* Shopify non configuré : le dire ici, pas au moment de la publication. */}
      {etat?.shopify && !etat.shopify.configure && (
        <p className="m-0 flex gap-2 rounded-xl px-4 py-3 text-[13px] leading-relaxed"
          style={{ background: "#FEF3C7", color: "#78350F" }} data-testid="shopify-manquant">
          <Info size={15} style={{ marginTop: 1, flexShrink: 0 }} />
          <span>
            La boutique Shopify n'est pas encore reliée côté serveur. Vous pouvez préparer vos fiches
            dès maintenant : elles partiront dès que la connexion sera en place.
          </span>
        </p>
      )}

      {/* ── Profil vendeur ─────────────────────────────────────── */}
      <section style={{ background: C.fond, border: `1px solid ${C.bord}`, borderRadius: 16, padding: 20 }}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="m-0 text-[15.5px] font-semibold" style={{ color: C.encre }}>Votre boutique</h2>
            <p className="m-0 mt-1 text-[13px]" style={{ color: C.doux }}>
              {etat?.profil_complet
                ? "Ce nom apparaît sur chacune de vos fiches produit."
                : "À compléter avant de déposer un premier produit."}
            </p>
          </div>
          {!editionProfil && (
            <button onClick={() => setEditionProfil(true)}
              style={{ borderRadius: 999, border: `1px solid ${C.bord}`, background: C.fond,
                       padding: "7px 16px", fontSize: 13, fontWeight: 600, color: C.texte, cursor: "pointer" }}>
              Modifier
            </button>
          )}
        </div>

        {editionProfil ? (
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <Etiquette obligatoire>Nom de la boutique</Etiquette>
              <input style={saisie} data-testid="profil-nom" value={profil?.nom_boutique || ""}
                onChange={(e) => setProfil((p) => ({ ...p, nom_boutique: e.target.value }))}
                placeholder="Atelier du Moulin" />
            </div>
            <div>
              <Etiquette obligatoire>Email de contact</Etiquette>
              <input style={saisie} data-testid="profil-email" value={profil?.email_contact || ""}
                onChange={(e) => setProfil((p) => ({ ...p, email_contact: e.target.value }))}
                placeholder="contact@atelier-du-moulin.fr" />
            </div>
            <div>
              <Etiquette>Téléphone</Etiquette>
              <input style={saisie} value={profil?.telephone || ""}
                onChange={(e) => setProfil((p) => ({ ...p, telephone: e.target.value }))} placeholder="06 12 34 56 78" />
            </div>
            <div>
              <Etiquette aide="14 chiffres. Nécessaire pour vendre en tant que professionnel.">SIRET</Etiquette>
              <input style={saisie} value={profil?.siret || ""}
                onChange={(e) => setProfil((p) => ({ ...p, siret: e.target.value }))} placeholder="812 345 678 00019" />
            </div>
            <div className="md:col-span-2">
              <Etiquette aide="Deux ou trois phrases sur ce que vous fabriquez ou revendez.">Présentation</Etiquette>
              <textarea style={{ ...saisie, minHeight: 80, resize: "vertical", fontFamily: "inherit" }}
                value={profil?.description || ""}
                onChange={(e) => setProfil((p) => ({ ...p, description: e.target.value }))} />
            </div>
            <label className="md:col-span-2 flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" data-testid="profil-conditions" checked={!!profil?.conditions_acceptees}
                onChange={(e) => setProfil((p) => ({ ...p, conditions_acceptees: e.target.checked }))}
                style={{ marginTop: 3, width: 15, height: 15, accentColor: C.navy }} />
              <span className="text-[13px] leading-relaxed" style={{ color: C.texte }}>
                Je certifie être autorisé à vendre les produits que je dépose, et j'accepte que Zayado
                vérifie chaque fiche avant sa mise en ligne.
              </span>
            </label>
            <div className="md:col-span-2">
              <button onClick={enregistrerProfil} disabled={occupe} data-testid="profil-enregistrer"
                style={{ borderRadius: 999, border: "none", background: C.navy, color: "#fff",
                         padding: "10px 22px", fontSize: 14, fontWeight: 600, cursor: "pointer", opacity: occupe ? .6 : 1 }}>
                {occupe ? "Enregistrement…" : "Enregistrer"}
              </button>
            </div>
          </div>
        ) : (
          <p className="m-0 mt-3 text-[14px] font-semibold" style={{ color: C.encre }}>
            {profil?.nom_boutique}
            <span className="ml-2 text-[13px] font-normal" style={{ color: C.doux }}>{profil?.email_contact}</span>
          </p>
        )}
      </section>

      {/* ── Fiches ─────────────────────────────────────────────── */}
      {edition ? (
        <Formulaire initial={edition} enregistrement={occupe}
          onAnnuler={() => setEdition(null)} onEnregistrer={enregistrerProduit} />
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="m-0 text-[15.5px] font-semibold" style={{ color: C.encre }}>Vos fiches produit</h2>
            <button onClick={() => setEdition({})} disabled={!etat?.profil_complet} data-testid="nouveau-produit"
              title={etat?.profil_complet ? "" : "Complétez d'abord votre boutique"}
              style={{ display: "inline-flex", alignItems: "center", gap: 6, borderRadius: 999, border: "none",
                       background: C.navy, color: "#fff", padding: "10px 20px", fontSize: 14, fontWeight: 600,
                       cursor: etat?.profil_complet ? "pointer" : "not-allowed", opacity: etat?.profil_complet ? 1 : .45 }}>
              <Plus size={15} /> Déposer un produit
            </button>
          </div>

          {produits.length > 0 ? (
            <div className="space-y-3">
              {produits.map((p) => (
                <LigneProduit key={p.id} produit={p} occupe={occupe}
                  onModifier={setEdition} onSupprimer={supprimer} onSoumettre={soumettre} />
              ))}
            </div>
          ) : (
            <div data-testid="vendeur-vide"
              style={{ background: C.fond, border: `1px dashed ${C.bord}`, borderRadius: 16,
                       padding: "40px 24px", textAlign: "center" }}>
              <Store size={26} color={C.tres_doux} />
              <p className="m-0 mt-3 text-[15px] font-semibold" style={{ color: C.encre }}>
                Aucun produit déposé pour l'instant.
              </p>
              <p className="m-0 mx-auto mt-1.5 max-w-md text-[13px] leading-relaxed" style={{ color: C.doux }}>
                {etat?.profil_complet
                  ? "Commencez par une fiche : un nom, une description, un prix et une photo suffisent pour l'envoyer à la vérification."
                  : "Complétez d'abord le nom et l'email de votre boutique ci-dessus."}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
