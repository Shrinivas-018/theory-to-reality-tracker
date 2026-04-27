/**
 * TreeMapVisualizer Component
 * 
 * Main component that orchestrates the tree visualization with:
 * - Layout calculation and node positioning
 * - State management for hover interactions
 * - Responsive layout recalculation
 * - Loading and empty states
 * - Animation coordination
 * - Accessibility support
 * 
 * Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1-2.7, 6.1-6.6, 8.1-8.5, 9.1-9.6, 11.1-11.5, 12.6
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { TreeMapVisualizerProps } from './types';
import { calculateLayout, sanitizeIdeaList } from './layoutEngine';
import IdeaNode from './IdeaNode';
import RelationshipEdge from './RelationshipEdge';

/**
 * TreeMapVisualizer renders an interactive hierarchical tree of ideas
 * 
 * Features:
 * - Hierarchical layout with ancestors above and descendants below root
 * - Interactive hover states with edge highlighting
 * - Responsive layout that adapts to container size
 * - Loading skeleton and empty state handling
 * - Smooth animations with Framer Motion
 * - Full keyboard accessibility
 * - Performance optimized with React.memo and useMemo
 */
export const TreeMapVisualizer: React.FC<TreeMapVisualizerProps> = ({
  rootIdea,
  ancestors,
  descendants,
  onNodeClick,
  isLoading = false,
}) => {
  // State management (Task 5.1)
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [containerDimensions, setContainerDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);

  // Data filtering and sorting (Task 5.2)
  // Filter to maximum 20 items and sort by start_year (most recent first)
  const sanitizedAncestors = useMemo(() => {
    const valid = sanitizeIdeaList(ancestors);
    return valid
      .sort((a, b) => b.start_year - a.start_year)
      .slice(0, 20);
  }, [ancestors]);

  const sanitizedDescendants = useMemo(() => {
    const valid = sanitizeIdeaList(descendants);
    return valid
      .sort((a, b) => b.start_year - a.start_year)
      .slice(0, 20);
  }, [descendants]);

  // Layout calculation and node positioning (Task 5.3)
  // Memoized to prevent unnecessary recalculations
  const { nodes, edges, layoutWidth } = useMemo(() => {
    return calculateLayout(
      rootIdea,
      sanitizedAncestors,
      sanitizedDescendants,
      containerDimensions.width,
      containerDimensions.height
    );
  }, [rootIdea, sanitizedAncestors, sanitizedDescendants, containerDimensions]);

  // Center scroll automatically if content overflows
  useEffect(() => {
    if (containerRef.current && layoutWidth > containerDimensions.width) {
      containerRef.current.scrollLeft = (layoutWidth - containerDimensions.width) / 2;
    }
  }, [layoutWidth, containerDimensions.width]);

  // Responsive layout recalculation (Task 5.4)
  // Measure container dimensions on mount and resize with debouncing
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setContainerDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };

    // Initial measurement
    updateDimensions();

    // Debounced resize handler (150ms debounce for performance)
    let timeoutId: NodeJS.Timeout;
    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(updateDimensions, 150);
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(timeoutId);
    };
  }, []);

  // Hover state management (Task 5.6)
  // Memoized callback to prevent unnecessary re-renders
  const handleNodeHover = useCallback((nodeId: string | null) => {
    setHoveredNodeId(nodeId);
  }, []);

  // Loading state (Task 5.7)
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  // Empty state (Task 5.7)
  // Display when both ancestors and descendants are empty
  if (sanitizedAncestors.length === 0 && sanitizedDescendants.length === 0) {
    return (
      <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 text-center shadow-inner">
        <p className="text-sm text-slate-400 italic">
          This is an emergent standalone concept with no explicitly mapped 
          ancestors or descendants in the knowledge graph.
        </p>
      </div>
    );
  }

  // Calculate dynamic height based on content
  const calculateContentHeight = () => {
    if (nodes.length === 0) return 400;
    
    // Find min and max Y positions
    const yPositions = nodes.map(n => n.position.y);
    const minY = Math.min(...yPositions);
    const maxY = Math.max(...yPositions);
    
    // Add padding (100px top, 100px bottom, plus node height)
    const contentHeight = maxY - minY + 200 + 80; // 80 is node height
    
    // Clamp between 400px and 2000px (higher max for full-page view)
    return Math.max(400, Math.min(contentHeight, 2000));
  };

  const contentHeight = calculateContentHeight();

  // Main render (Task 5.5, 5.8)
  return (
    <div
      ref={containerRef}
      role="tree"
      aria-label="Evolutionary lineage tree"
      className="relative w-full bg-slate-950 rounded-xl border border-slate-800 overflow-auto shadow-inner"
      style={{ height: `${contentHeight}px`, maxHeight: '100%' }}
    >
      {/* Background Grid Pattern */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.4) 1px, transparent 0)',
          backgroundSize: '32px 32px'
        }}
        aria-hidden="true"
      />

      {/* SVG Layer for Edges (Task 5.5) */}
      <svg
        className="absolute inset-0 pointer-events-none"
        style={{ zIndex: 1, minHeight: `${contentHeight}px`, minWidth: `${layoutWidth}px`, width: layoutWidth > containerDimensions.width ? `${layoutWidth}px` : '100%' }}
        aria-hidden="true"
      >
        {edges.map((edge, index) => (
          <RelationshipEdge
            key={edge.id}
            sourcePosition={edge.sourcePosition}
            targetPosition={edge.targetPosition}
            edgeType={edge.type}
            isHighlighted={
              hoveredNodeId === edge.sourceId || hoveredNodeId === edge.targetId
            }
            animationDelay={index}
          />
        ))}
      </svg>

      {/* Node Layer (Task 5.5) */}
      <div className="absolute inset-0" style={{ zIndex: 2, minHeight: `${contentHeight}px`, minWidth: `${layoutWidth}px`, width: layoutWidth > containerDimensions.width ? `${layoutWidth}px` : '100%' }}>
        {nodes.map((node, index) => (
          <IdeaNode
            key={node.id}
            idea={node.idea}
            position={node.position}
            isRoot={node.isRoot}
            isHovered={hoveredNodeId === node.id}
            onHover={handleNodeHover}
            onClick={onNodeClick}
            animationDelay={index}
          />
        ))}
      </div>
    </div>
  );
};

// Performance optimization (Task 5.9)
// Memoize component to prevent unnecessary re-renders
export default React.memo(TreeMapVisualizer, (prevProps, nextProps) => {
  return (
    prevProps.rootIdea.id === nextProps.rootIdea.id &&
    prevProps.ancestors === nextProps.ancestors &&
    prevProps.descendants === nextProps.descendants &&
    prevProps.isLoading === nextProps.isLoading &&
    prevProps.onNodeClick === nextProps.onNodeClick
  );
});
