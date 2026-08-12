"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { PropsWithChildren } from "react";

export default function MotionPanel({ children, className, id }: PropsWithChildren<{ className?: string; id?: string }>) {
  const reduced = useReducedMotion();
  return (
    <motion.article
      id={id}
      className={className}
      initial={reduced ? false : { opacity: 0, y: 10 }}
      whileInView={reduced ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-8%" }}
      transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.article>
  );
}
