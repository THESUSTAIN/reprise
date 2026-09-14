import React, { useRef, useState } from "react";
import "@/App.css";
import { AnimatePresence } from "framer-motion";
import { Toaster } from "sonner";
import { AppProvider, useApp } from "@/context/AppContext";
import { Header } from "@/components/Header";
import { Hero } from "@/components/Hero";
import { Gallery } from "@/components/Gallery";
import { TemplateDetail } from "@/components/TemplateDetail";
import { FavoritesPanel } from "@/components/FavoritesPanel";

const Shell = () => {
  const { t, theme } = useApp();
  const galleryRef = useRef(null);
  const [selected, setSelected] = useState(null);
  const [favOpen, setFavOpen] = useState(false);

  const scrollToGallery = () =>
    galleryRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  const scrollTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  return (
    <div className="App grain min-h-screen">
      <Toaster position="bottom-center" theme={theme} richColors />
      <Header onFavoritesClick={() => setFavOpen(true)} onLogoClick={scrollTop} />

      <main className="relative z-10">
        <Hero onExplore={scrollToGallery} onFavorites={() => setFavOpen(true)} />
        <Gallery ref={galleryRef} onOpen={setSelected} />
      </main>

      <footer className="relative z-10 border-t border-border py-10 text-center">
        <p className="font-display text-lg font-bold">{t("brand")}</p>
        <p className="mt-1 text-sm text-muted-foreground">{t("footer_note")}</p>
      </footer>

      <AnimatePresence>
        {selected && <TemplateDetail template={selected} onClose={() => setSelected(null)} />}
      </AnimatePresence>
      <AnimatePresence>
        {favOpen && <FavoritesPanel onClose={() => setFavOpen(false)} onOpen={setSelected} />}
      </AnimatePresence>
    </div>
  );
};

function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}

export default App;
