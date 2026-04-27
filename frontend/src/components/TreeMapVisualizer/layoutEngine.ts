/**
 * Layout Engine for TreeMapVisualizer
 * 
 * Calculates node positions in a hierarchical tree structure with:
 * - Ancestors positioned above the root
 * - Root node at the center
 * - Descendants positioned below the root
 * - Multi-row layout for more than 5 nodes per level
 * - Responsive sizing based on viewport width
 */

import { Idea, NodePosition, LayoutConfig, TreeNode, TreeEdge } from './types';

/**
 * Get responsive node width based on viewport width
 * @param viewportWidth - Current viewport width in pixels
 * @returns Node width in pixels
 */
export function getResponsiveNodeWidth(viewportWidth: number): number {
  if (viewportWidth < 640) return 120; // mobile
  if (viewportWidth < 768) return 160; // tablet
  return 200; // desktop
}

/**
 * Get responsive layout configuration based on viewport width
 * @param viewportWidth - Current viewport width in pixels
 * @returns Layout configuration object
 */
export function getLayoutConfig(viewportWidth: number): LayoutConfig {
  const nodeWidth = getResponsiveNodeWidth(viewportWidth);
  
  return {
    levelHeight: viewportWidth < 640 ? 100 : viewportWidth < 768 ? 110 : 120,
    nodeWidth,
    nodeHeight: 80,
    minSpacing: 16,
    maxNodesPerRow: viewportWidth < 640 ? 3 : viewportWidth < 768 ? 4 : 5,
    maxRowsPerLevel: 4,
    rowSpacing: 80,
  };
}

/**
 * Distribute nodes horizontally across one or more rows
 * @param nodes - Array of ideas to position
 * @param containerWidth - Available horizontal space
 * @param baseY - Base Y position for the level
 * @param level - Level type (ancestor/root/descendant)
 * @param config - Layout configuration
 * @returns Array of positioned nodes
 */
export function distributeNodesHorizontally(
  nodes: Idea[],
  containerWidth: number,
  baseY: number,
  level: 'ancestor' | 'root' | 'descendant',
  config: LayoutConfig
): NodePosition[] {
  const positions: NodePosition[] = [];
  const { nodeWidth, maxNodesPerRow, rowSpacing, minSpacing, maxRowsPerLevel } = config;
  
  // Limit to maxRowsPerLevel to prevent excessive height
  const totalRows = Math.ceil(nodes.length / maxNodesPerRow);
  const rows = Math.min(totalRows, maxRowsPerLevel);
  const limitedNodes = nodes.slice(0, rows * maxNodesPerRow);
  
  for (let row = 0; row < rows; row++) {
    const startIdx = row * maxNodesPerRow;
    const endIdx = Math.min((row + 1) * maxNodesPerRow, limitedNodes.length);
    const nodesInRow = endIdx - startIdx;
    
    const totalWidth = nodesInRow * nodeWidth + (nodesInRow - 1) * minSpacing;
    const startX = (containerWidth - totalWidth) / 2;
    
    for (let i = 0; i < nodesInRow; i++) {
      const nodeIdx = startIdx + i;
      positions.push({
        x: startX + i * (nodeWidth + minSpacing) + nodeWidth / 2,
        y: baseY + row * rowSpacing,
        level,
      });
    }
  }
  
  return positions;
}

/**
 * Calculate layout for all nodes in the tree
 * @param rootIdea - The central root node
 * @param ancestors - Array of ancestor ideas
 * @param descendants - Array of descendant ideas
 * @param containerWidth - Available horizontal space
 * @param containerHeight - Available vertical space
 * @returns Object containing positioned nodes and edges
 */
export function calculateLayout(
  rootIdea: Idea,
  ancestors: Idea[],
  descendants: Idea[],
  containerWidth: number,
  containerHeight: number = 600
): { nodes: TreeNode[]; edges: TreeEdge[]; layoutWidth: number } {
  const config = getLayoutConfig(containerWidth);
  
  const maxNodesInRow = Math.max(
    1,
    Math.min(ancestors.length, config.maxNodesPerRow),
    Math.min(descendants.length, config.maxNodesPerRow)
  );
  
  const requiredWidth = maxNodesInRow * config.nodeWidth + Math.max(0, maxNodesInRow - 1) * config.minSpacing + 100;
  const layoutWidth = Math.max(containerWidth, requiredWidth);
  
  const nodes: TreeNode[] = [];
  const edges: TreeEdge[] = [];
  
  // Calculate total height needed for multi-row layouts
  const ancestorRows = Math.min(
    Math.ceil(ancestors.length / config.maxNodesPerRow),
    config.maxRowsPerLevel
  );
  const descendantRows = Math.min(
    Math.ceil(descendants.length / config.maxNodesPerRow),
    config.maxRowsPerLevel
  );
  
  const ancestorHeight = ancestorRows > 0 ? config.levelHeight + (ancestorRows - 1) * config.rowSpacing : 0;
  const descendantHeight = descendantRows > 0 ? config.levelHeight + (descendantRows - 1) * config.rowSpacing : 0;
  
  // Position root node with padding from top
  const topPadding = 100;
  const rootY = topPadding + ancestorHeight + config.nodeHeight / 2;
  
  // Position root node at center horizontally
  const rootPosition: NodePosition = {
    x: layoutWidth / 2,
    y: rootY,
    level: 'root',
  };
  
  nodes.push({
    id: rootIdea.id,
    idea: rootIdea,
    position: rootPosition,
    level: 'root',
    isRoot: true,
  });
  
  // Position ancestors above root
  if (ancestors.length > 0) {
    const ancestorY = rootY - config.levelHeight;
    const ancestorPositions = distributeNodesHorizontally(
      ancestors,
      layoutWidth,
      ancestorY,
      'ancestor',
      config
    );
    
    // Only create nodes and edges for positioned ancestors (respects maxRowsPerLevel)
    ancestorPositions.forEach((position, index) => {
      const ancestor = ancestors[index];
      nodes.push({
        id: ancestor.id,
        idea: ancestor,
        position,
        level: 'ancestor',
        isRoot: false,
      });
      
      // Create edge from ancestor to root
      edges.push({
        id: `${ancestor.id}-${rootIdea.id}`,
        sourceId: ancestor.id,
        targetId: rootIdea.id,
        sourcePosition: { x: position.x, y: position.y },
        targetPosition: { x: rootPosition.x, y: rootPosition.y },
        type: 'ancestor',
      });
    });
  }
  
  // Position descendants below root
  if (descendants.length > 0) {
    const descendantY = rootY + config.levelHeight;
    const descendantPositions = distributeNodesHorizontally(
      descendants,
      layoutWidth,
      descendantY,
      'descendant',
      config
    );
    
    // Only create nodes and edges for positioned descendants (respects maxRowsPerLevel)
    descendantPositions.forEach((position, index) => {
      const descendant = descendants[index];
      nodes.push({
        id: descendant.id,
        idea: descendant,
        position,
        level: 'descendant',
        isRoot: false,
      });
      
      // Create edge from root to descendant
      edges.push({
        id: `${rootIdea.id}-${descendant.id}`,
        sourceId: rootIdea.id,
        targetId: descendant.id,
        sourcePosition: { x: rootPosition.x, y: rootPosition.y },
        targetPosition: { x: position.x, y: position.y },
        type: 'descendant',
      });
    });
  }
  
  return { nodes, edges, layoutWidth };
}

/**
 * Validate idea data structure
 * @param idea - Idea object to validate
 * @returns True if idea is valid
 */
export function validateIdeaData(idea: any): idea is Idea {
  return (
    typeof idea?.id === 'string' &&
    typeof idea?.title === 'string' &&
    typeof idea?.start_year === 'number'
  );
}

/**
 * Sanitize and filter idea list
 * @param ideas - Array of ideas to sanitize
 * @returns Filtered array of valid ideas
 */
export function sanitizeIdeaList(ideas: any[]): Idea[] {
  return ideas.filter(validateIdeaData);
}
