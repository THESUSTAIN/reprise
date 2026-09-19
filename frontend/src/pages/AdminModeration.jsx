import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Store, Loader2, Check, X, ArrowLeft, AlertCircle, ExternalLink, ShieldAlert,
} from "lucide-react";
import { toast } from "sonner";
import { authMe, getModerationQueue, publishVendeurProduit, rejectVendeurProduit } from "../lib/api";

/* Même palette claire que EspaceVendeur.jsx — cohérence visuelle entre le
   côté vendeur et le côté admin de la marketplace. */
const C = {
  encre: "#111827", texte: "#374151", doux: "#6B7280", tres_doux: "#9CA3AF",
  bord: "#E5E7EB", fond: "#FFFFFF", fond2: "#F9FAFB", navy: "#0B1B3A",
};

function RefuserModal({ produit, onClose, onConfirm, envoi }) {
  const [motif, setMotif] = useState("");
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(17,24,39,.55)", display: "flex", alignItems: "center", justifyContent: "center", padding: 16, zIndex: 50 }}>
      <div style={{ background: C.fond, borderRadius: 16, padding: 22, width: "100%", maxWidth: 440 }}>
        <h3 style={{ margin: "0 0 6px", fontSize: 15, fontWeight: 700, color: C.encre }}>Refuser « {produit.titre} »</h3>
        <p style={{ margin: "0 0 12px", fontSize: 12.5, color: C.doux }}>
          Le motif est obligatoire — le vendeur doit savoir précisément quoi corriger.
        </p>
        <textarea value={motif} onChange={(e) => setMotif(e.target.value)} rows={4}
                  placeholder="Ex : photos trop sombres, description incomplète, prix incohérent…"
                  style={{ width: "100%", border: `1px solid ${C.bord}`, borderRadius: 10, padding: "9px 11px", fontSize: 13, resize: "vertical", boxSizing: "border-box" }} />
        <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
          <button onClick={() => onConfirm(motif)} disabled={!motif.trim() || envoi}
                  style={{ flex: 1, background: "#B91C1C", color: "#fff", border: "none", borderRadius: 999, padding: "9px 0", fontSize: 13, fontWeight: 600, cursor: "pointer", opacity: (!motif.trim() || envoi) ? .5 : 1 }}>
            {envoi ? "Envoi…" : "Confirmer le refus"}
          </button>
          <button onClick={onClose} disabled={envoi}
                  style={{ flex: 1, background: C.fond2, color: C.texte, border: `1px solid ${C.bord}`, borderRadius: 999, padding: "9px 0", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
            Annuler
          </button>
        </div>
      </div>
    </div>
  );
}

function ProduitModeration({ produit, onPublier, onRefuser, occupe }) {
  const image = (produit.images || [])[0];
  return (
    <div style={{ background: C.fond, border: `1px solid ${C.bord}`, borderRadius: 14, padding: 16, display: "flex", gap: 14 }}>
      <div style={{ width: 84, height: 84, borderRadius: 10, overflow: "hidden", flexShrink: 0, background: C.fond2, display: "flex", alignItems: "center", justifyContent: "center" }}>
        {image ? <img src={image} alt={produit.titre} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : <Store size={20} color={C.tres_doux} />}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: C.encre }}>{produit.titre}</div>
            <div style={{ fontSize: 12, color: C.doux, marginTop: 2 }}>
              Vendeur : {produit.vendeur || "—"} · {produit.prix ? `${produit.prix} €` : "Prix non renseigné"}
              {produit.categorie ? ` · ${produit.categorie}` : ""}
            </div>
          </div>
        </div>
        {produit.description && (
          <p style={{ margin: "8px 0 0", fontSize: 12.5, color: C.texte, lineHeight: 1.5 }}>
            {produit.description.length > 220 ? produit.description.slice(0, 220) + "…" : produit.description}
          </p>
        )}
        <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
          <button onClick={onPublier} disabled={occupe}
                  style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "#047857", color: "#fff", border: "none", borderRadius: 999, padding: "7px 14px", fontSize: 12.5, fontWeight: 600, cursor: "pointer", opacity: occupe ? .6 : 1 }}>
            {occupe ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />} Publier sur Shopify
          </button>
          <button onClick={onRefuser} disabled={occupe}
                  style={{ display: "inline-flex", alignItems: "center", gap: 6, background: C.fond2, color: "#B91C1C", border: `1px solid ${C.bord}`, borderRadius: 999, padding: "7px 14px", fontSize: 12.5, fontWeight: 600, cursor: "pointer", opacity: occupe ? .6 : 1 }}>
            <X size={13} /> Refuser
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AdminModeration() {
  const navigate = useNavigate();
  const [autorise, setAutorise] = useState(null); // null = vérification en cours
  const [chargement, setChargement] = useState(true);
  const [file, setFile] = useState([]);
  const [occupePid, setOccupePid] = useState(null);
  const [aRefuser, setARefuser] = useState(null); // produit en cours de refus (ouvre la modale)

  const charger = useCallback(async () => {
    setChargement(true);
    try {
      const data = await getModerationQueue();
      setFile(data.items || data || []);
    } catch (e) {
      if (e?.response?.status !== 403) toast.error("Impossible de charger la file de modération.");
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => {
    authMe().then((user) => {
      const ok = user && ["admin", "super_admin"].includes(user.role);
      setAutorise(ok);
      if (ok) charger();
    }).catch(() => setAutorise(false));
  }, [charger]);

  const publier = async (produit) => {
    setOccupePid(produit.id);
    try {
      await publishVendeurProduit(produit.id, produit._vendeur_user_id);
      toast.success(`« ${produit.titre} » publié sur Shopify.`);
      setFile((f) => f.filter((p) => p.id !== produit.id));
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Shopify a refusé la publication.");
    } finally {
      setOccupePid(null);
    }
  };

  const confirmerRefus = async (motif) => {
    const produit = aRefuser;
    setOccupePid(produit.id);
    try {
      await rejectVendeurProduit(produit.id, produit._vendeur_user_id, motif);
      toast.success(`« ${produit.titre} » refusé — le vendeur voit le motif.`);
      setFile((f) => f.filter((p) => p.id !== produit.id));
      setARefuser(null);
    } catch {
      toast.error("Impossible d'enregistrer le refus.");
    } finally {
      setOccupePid(null);
    }
  };

  if (autorise === null) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: C.fond2 }}>
        <Loader2 size={22} className="animate-spin" color={C.doux} />
      </div>
    );
  }

  if (!autorise) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: C.fond2, gap: 12, padding: 24, textAlign: "center" }}>
        <ShieldAlert size={30} color="#B91C1C" />
        <p style={{ margin: 0, fontSize: 14, color: C.texte, fontWeight: 600 }}>Réservé à l'équipe Zayado.</p>
        <button onClick={() => navigate("/")} style={{ color: C.navy, fontSize: 13, background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}>
          Retour à l'accueil
        </button>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: C.fond2, fontFamily: "Inter, system-ui, sans-serif" }}>
      <div style={{ maxWidth: 760, margin: "0 auto", padding: "32px 20px 60px" }}>
        <button onClick={() => navigate(-1)} style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "none", border: "none", color: C.doux, fontSize: 12.5, cursor: "pointer", marginBottom: 18, padding: 0 }}>
          <ArrowLeft size={14} /> Retour
        </button>
        <h1 style={{ fontSize: 21, fontWeight: 800, color: C.encre, margin: "0 0 4px" }}>Modération marketplace</h1>
        <p style={{ fontSize: 13, color: C.doux, margin: "0 0 22px" }}>
          Chaque fiche approuvée est créée réellement dans Shopify — vérifiez avant de publier.
        </p>

        {chargement && (
          <div style={{ display: "flex", justifyContent: "center", padding: "60px 0" }}>
            <Loader2 size={20} className="animate-spin" color={C.doux} />
          </div>
        )}

        {!chargement && file.length === 0 && (
          <div style={{ background: C.fond, border: `1px dashed ${C.bord}`, borderRadius: 14, padding: 40, textAlign: "center" }}>
            <Check size={26} color="#047857" style={{ marginBottom: 8 }} />
            <p style={{ margin: 0, fontSize: 13.5, color: C.texte, fontWeight: 600 }}>File vide</p>
            <p style={{ margin: "4px 0 0", fontSize: 12.5, color: C.doux }}>Aucune fiche vendeur en attente de vérification.</p>
          </div>
        )}

        {!chargement && file.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {file.map((p) => (
              <ProduitModeration key={p.id} produit={p} occupe={occupePid === p.id}
                                  onPublier={() => publier(p)} onRefuser={() => setARefuser(p)} />
            ))}
          </div>
        )}
      </div>

      {aRefuser && (
        <RefuserModal produit={aRefuser} envoi={occupePid === aRefuser.id}
                      onClose={() => setARefuser(null)} onConfirm={confirmerRefus} />
      )}
    </div>
  );
}
