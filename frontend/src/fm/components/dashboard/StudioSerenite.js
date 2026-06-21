import React from "react";
import { Heart, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

/**
 * Studio Sérénité — promotes the "30% Humain" methodology on the Dashboard.
 * Sits between the hero and the cards grid.
 */
export default function StudioSerenite({ missionToday }) {
  const navigate = useNavigate();
  const headline =
    missionToday?.coach_message ||
    missionToday?.title ||
    "Ralentir pour décider juste.";
  const subline =
    missionToday?.coach_subline ||
    "Aujourd'hui, votre co-pilote vous propose de garder une seule décision stratégique — et de déléguer le reste à l'IA.";

  return (
    <section
      data-testid="studio-serenite"
      className="mb-6 rounded-3xl overflow-hidden border border-[#E8DCC3] relative grain-overlay"
      style={{
        background:
          "linear-gradient(135deg, #1F3B73 0%, #2A4D8F 100%)",
        color: "#F6F3EE",
      }}
    >
      <div className="relative px-6 sm:px-10 py-7 grid md:grid-cols-[1fr_auto] gap-6 items-center">
        <div className="flex items-start gap-4">
          <div
            className="w-12 h-12 shrink-0 rounded-2xl grid place-items-center"
            style={{ background: "rgba(201,166,107,0.20)", color: "#C9A66B" }}
          >
            <Heart size={20} />
          </div>
          <div className="min-w-0">
            <div
              className="text-[10.5px] tracking-[0.22em] uppercase font-semibold mb-1.5"
              style={{ color: "#C9A66B" }}
            >
              Studio Sérénité · 30 % Humain
            </div>
            <h2 className="font-display text-[22px] sm:text-[26px] leading-tight mb-1.5">
              « {headline} »
            </h2>
            <p className="text-[13.5px] leading-relaxed opacity-85 max-w-[640px]">
              {subline}
            </p>
          </div>
        </div>

        <button
          onClick={() => navigate("/bien-etre")}
          data-testid="studio-serenite-cta"
          className="inline-flex items-center gap-2 px-5 h-11 rounded-full bg-[#C9A66B] hover:bg-[#B8965B] text-[#1F3B73] text-[13.5px] font-semibold transition shrink-0 justify-self-start md:justify-self-end"
        >
          Ouvrir mon rituel
          <ArrowRight size={14} />
        </button>
      </div>
    </section>
  );
}
