/**
 * RelationshipEdge Component
 * 
 * Renders SVG paths connecting related nodes with:
 * - Bezier curve path calculation
 * - Color coding by edge type (pink for ancestors, violet for descendants)
 * - Stroke drawing animation
 * - Hover state opacity changes
 * - Accessibility attributes
 * - Motion preferences support (prefers-reduced-motion)
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { RelationshipEdgeProps } from './types';

/**
 * Check if user prefers reduced motion
 */
const prefersReducedMotion = () => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Calculate Bezier curve path between two points
 * @param source - Source position {x, y}
 * @param target - Target position {x, y}
 * @returns SVG path data string
 */
export function calculateEdgePath(
  source: { x: number; y: number },
  target: { x: number; y: number }
): string {
  const midY = (source.y + target.y) / 2;
  
  // Control points for smooth curve
  const cp1 = { x: source.x, y: midY };
  const cp2 = { x: target.x, y: midY };
  
  return `M ${source.x} ${source.y} C ${cp1.x} ${cp1.y}, ${cp2.x} ${cp2.y}, ${target.x} ${target.y}`;
}

/**
 * RelationshipEdge component renders a connection line between nodes
 */
export const RelationshipEdge: React.FC<RelationshipEdgeProps> = ({
  sourcePosition,
  targetPosition,
  edgeType,
  isHighlighted,
  animationDelay,
}) => {
  // Check motion preferences once per component
  const reducedMotion = useMemo(() => prefersReducedMotion(), []);
  
  const pathData = calculateEdgePath(sourcePosition, targetPosition);
  
  // Color based on edge type with glowing effect
  const strokeColor = edgeType === 'ancestor' 
    ? 'hsl(330, 90%, 70%)' // vibrant pink
    : 'hsl(270, 90%, 70%)'; // vibrant violet
  
  // Create a glow filter string
  const glowColor = edgeType === 'ancestor' ? 'rgba(244, 114, 182, 0.6)' : 'rgba(167, 139, 250, 0.6)';
  
  return (
    <motion.path
      d={pathData}
      stroke={strokeColor}
      strokeWidth={isHighlighted ? 3 : 2}
      fill="none"
      style={{ filter: isHighlighted ? `drop-shadow(0 0 6px ${glowColor})` : 'none' }}
      initial={{
        pathLength: reducedMotion ? 1 : 0,
        opacity: reducedMotion ? (isHighlighted ? 0.9 : 0.4) : 0,
      }}
      animate={{
        pathLength: 1,
        opacity: isHighlighted ? 0.9 : 0.4,
      }}
      transition={{
        pathLength: { 
          duration: reducedMotion ? 0 : 0.6, 
          ease: 'easeInOut', 
          delay: reducedMotion ? 0 : animationDelay * 0.05 
        },
        opacity: { 
          duration: reducedMotion ? 0 : (isHighlighted ? 0.2 : 0.3), 
          delay: reducedMotion ? 0 : animationDelay * 0.05,
          ease: 'easeInOut'
        },
      }}
      aria-hidden="true"
    />
  );
};

export default RelationshipEdge;
