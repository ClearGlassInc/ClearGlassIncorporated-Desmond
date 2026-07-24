"use client";

// Add-to-cart button. Embeds in server-rendered product listings; on click it
// pushes the governed catalog line into the cart and briefly confirms.
import { useState } from "react";
import type { Product } from "./catalog";
import { useCart } from "./cart";

export function AddToCart({ product, block = false }: { product: Product; block?: boolean }) {
  const { add } = useCart();
  const [added, setAdded] = useState(false);

  function onClick(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    add(product, 1);
    setAdded(true);
    setTimeout(() => setAdded(false), 1200);
  }

  return (
    <button
      onClick={onClick}
      className={`btn-neon${added ? " btn-neon--accent" : ""}`}
      style={{
        width: block ? "100%" : undefined,
        marginTop: 12,
      }}
    >
      {added ? "Added ✓" : "Add to cart"}
    </button>
  );
}
