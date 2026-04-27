/**
 * TypeScript type definitions for TreeMapVisualizer component
 */

/**
 * Idea data structure matching the backend API response
 */
export interface Idea {
  id: string;
  title: string;
  description?: string;
  stage: string;
  start_year: number;
  end_year?: number;
  category: string;
  laureates?: string[];
  keywords?: string[];
  influence_score?: number;
  chain?: string;
}

/**
 * Props for the main TreeMapVisualizer component
 */
export interface TreeMapVisualizerProps {
  rootIdea: Idea;
  ancestors: Idea[];
  descendants: Idea[];
  onNodeClick: (ideaId: string) => void;
  isLoading?: boolean;
}

/**
 * Internal state management for the tree map
 */
export interface TreeMapState {
  nodePositions: Map<string, NodePosition>;
  hoveredNodeId: string | null;
  containerDimensions: { width: number; height: number };
}

/**
 * Position and level information for a node in the tree
 */
export interface NodePosition {
  x: number;
  y: number;
  level: 'ancestor' | 'root' | 'descendant';
}

/**
 * Complete node data structure including idea and position
 */
export interface TreeNode {
  id: string;
  idea: Idea;
  position: NodePosition;
  level: 'ancestor' | 'root' | 'descendant';
  isRoot: boolean;
}

/**
 * Edge data structure connecting two nodes
 */
export interface TreeEdge {
  id: string;
  sourceId: string;
  targetId: string;
  sourcePosition: { x: number; y: number };
  targetPosition: { x: number; y: number };
  type: 'ancestor' | 'descendant';
}

/**
 * Configuration for layout calculations
 */
export interface LayoutConfig {
  levelHeight: number;        // 120px - vertical spacing between levels
  nodeWidth: number;          // 200px (desktop), 120px (mobile)
  nodeHeight: number;         // 80px
  minSpacing: number;         // 16px - minimum horizontal spacing
  maxNodesPerRow: number;     // 5 - maximum nodes per row before wrapping
  maxRowsPerLevel: number;    // 4 - maximum rows per level
  rowSpacing: number;         // 80px - vertical spacing between rows
}

/**
 * Props for the IdeaNode component
 */
export interface IdeaNodeProps {
  idea: Idea;
  position: NodePosition;
  isRoot: boolean;
  isHovered: boolean;
  onHover: (ideaId: string | null) => void;
  onClick: (ideaId: string) => void;
  animationDelay: number;
}

/**
 * Props for the RelationshipEdge component
 */
export interface RelationshipEdgeProps {
  sourcePosition: { x: number; y: number };
  targetPosition: { x: number; y: number };
  edgeType: 'ancestor' | 'descendant';
  isHighlighted: boolean;
  animationDelay: number;
}
