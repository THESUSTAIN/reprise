import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

// Glassmorphism card with staggered entrance and subtle hover glow.
export const GlassCard = React.forwardRef(function GlassCard(
  { children, className, delay = 0, glow = "gold", hover = true, ...props },
  ref
) {
  const glowMap = {
    gold: "hover:shadow-[0_0_28px_rgba(212,175,55,0.16)]",
    emerald: "hover:shadow-[0_0_28px_rgba(16,185,129,0.16)]",
    teal: "hover:shadow-[0_0_28px_rgba(20,184,166,0.14)]",
    none: "",
  };
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "glass p-5 relative overflow-hidden",
        hover && "transition-[border-color,box-shadow,transform] duration-300 hover:-translate-y-0.5",
        hover && glowMap[glow],
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
});

export default GlassCard;
