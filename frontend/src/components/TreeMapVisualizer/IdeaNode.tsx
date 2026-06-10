/**
 * IdeaNode Component
 * 
 * Renders an individual idea card in the tree map with:
 * - Title and year display
 * - Root node styling (gradient border) or standard styling
 * - Hover and click interactions
 * - Framer Motion animations
 * - Responsive sizing
 * - Accessibility attributes
 * - Motion preferences support (prefers-reduced-motion)
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { IdeaNodeProps } from './types';

/**
 * Check if user prefers reduced motion
 */
const prefersReducedMotion = () => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Animation variants for node fade-in
 */
const getNodeVariants = (reducedMotion: boolean) => ({
  hidden: { opacity: reducedMotion ? 1 : 0, scale: reducedMotion ? 1 : 0.8 },
  visible: (delay: number) => ({
    opacity: 1,
    scale: 1,
    transition: {
      duration: reducedMotion ? 0 : 0.3,
      delay: reducedMotion ? 0 : delay * 0.05, // 50ms stagger
      ease: 'easeOut',
    },
  }),
});

/**
 * Animation variants for hover effect
 */
const getHoverVariants = (reducedMotion: boolean) => ({
  rest: { scale: 1 },
  hover: {
    scale: reducedMotion ? 1 : 1.05,
    transition: { duration: reducedMotion ? 0 : 0.2, ease: 'easeOut' },
  },
});

/**
 * Get stage label from stage string
 */
const getStageLabel = (stage: string) => {
  return stage.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
};

/**
 * IdeaNode component renders a single node card in the tree
 */
export const IdeaNode: React.FC<IdeaNodeProps> = ({
  idea,
  position,
  isRoot,
  isHovered,
  onHover,
  onClick,
  animationDelay,
}) => {
  // Check motion preferences once per component
  const reducedMotion = useMemo(() => prefersReducedMotion(), []);
  const nodeVariants = useMemo(() => getNodeVariants(reducedMotion), [reducedMotion]);
  const hoverVariants = useMemo(() => getHoverVariants(reducedMotion), [reducedMotion]);

  const handleClick = () => {
    if (!isRoot) {
      onClick(idea.id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isRoot && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick(idea.id);
    }
  };

  return (
    <motion.div
      variants={nodeVariants}
      initial="hidden"
      animate="visible"
      custom={animationDelay}
      className="absolute"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: 'translate(-50%, -50%)',
      }}
    >
      <motion.div
        variants={hoverVariants}
        initial="rest"
        whileHover={!isRoot ? 'hover' : 'rest'}
        onHoverStart={() => onHover(idea.id)}
        onHoverEnd={() => onHover(null)}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        tabIndex={isRoot ? -1 : 0}
        role="treeitem"
        aria-label={`${idea.title}, ${idea.start_year}`}
        aria-current={isRoot ? 'true' : undefined}
        className={`
          ${isRoot 
            ? 'bg-gradient-to-br from-violet-600 via-fuchsia-600 to-pink-600 p-[2px] rounded-xl shadow-[0_0_30px_rgba(217,70,239,0.3)]' 
            : 'bg-slate-900/80 backdrop-blur-md border border-slate-700 shadow-md'
          }
          ${!isRoot && 'cursor-pointer hover:border-violet-500/60 hover:shadow-[0_0_15px_rgba(139,92,246,0.4)] hover:bg-slate-800'}
          ${!isRoot && isHovered && 'border-violet-400 shadow-[0_0_20px_rgba(139,92,246,0.5)]'}
          transition-all duration-300 ease-out
          focus:outline-none focus:ring-2 focus:ring-pink-500 focus:ring-offset-2 focus:ring-offset-slate-950
          w-[120px] max-w-[120px]
          sm:w-[160px] sm:max-w-[160px]
          md:w-[200px] md:max-w-[200px]
        `}
      >
        <div className={`
          ${isRoot ? 'bg-slate-950 rounded-[10px] px-6 py-3 shadow-inner' : 'px-2 py-2 sm:px-2.5 sm:py-2.5 md:px-3 md:py-3'}
          flex flex-col items-center
        `}>
          <span className={`
            ${isRoot ? 'font-bold text-white tracking-wide' : 'font-medium text-slate-200'}
            text-center line-clamp-2 leading-tight
            text-[11px] sm:text-[12px] md:text-[13px]
            max-w-full
          `}>
            {idea.title}
          </span>
          
          {isRoot ? (
            <Badge variant="secondary" className="mt-2 text-[9px] bg-violet-500/20 text-violet-200 border-violet-500/30 backdrop-blur-sm px-2 py-0.5">
              {idea.start_year} · {getStageLabel(idea.stage)}
            </Badge>
          ) : (
            <span className="text-[9px] text-slate-400 mt-1 font-mono tracking-wider">
              {idea.start_year}
            </span>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default IdeaNode;
