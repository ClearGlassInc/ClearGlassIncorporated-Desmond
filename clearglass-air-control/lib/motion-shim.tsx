'use client';

import React from 'react';

type MotionProps = Record<string, unknown> & {
  children?: React.ReactNode;
  animate?: unknown;
  initial?: unknown;
  transition?: unknown;
  whileHover?: unknown;
  whileTap?: unknown;
};

const ignoredMotionProps = new Set(['animate', 'initial', 'transition', 'whileHover', 'whileTap']);

function createMotionElement(tag: keyof React.JSX.IntrinsicElements) {
  const MotionElement = React.forwardRef<unknown, MotionProps>(({ children, ...props }, ref) => {
    const passthrough = Object.fromEntries(
      Object.entries(props).filter(([key]) => !ignoredMotionProps.has(key)),
    );

    return React.createElement(tag, { ...passthrough, ref } as Record<string, unknown>, children);
  });
  MotionElement.displayName = `MotionShim.${String(tag)}`;
  return MotionElement;
}

export const motion = {
  button: createMotionElement('button'),
  circle: createMotionElement('circle'),
  div: createMotionElement('div'),
  section: createMotionElement('section'),
};
