/**
 * Unit tests for layout engine functions
 */

import { describe, it, expect } from 'vitest';
import {
  getResponsiveNodeWidth,
  getLayoutConfig,
  distributeNodesHorizontally,
  calculateLayout,
  validateIdeaData,
  sanitizeIdeaList,
} from '../layoutEngine';
import { Idea } from '../types';

describe('layoutEngine', () => {
  describe('getResponsiveNodeWidth', () => {
    it('should return 120px for mobile viewport (< 640px)', () => {
      expect(getResponsiveNodeWidth(360)).toBe(120);
      expect(getResponsiveNodeWidth(639)).toBe(120);
    });

    it('should return 160px for tablet viewport (640-768px)', () => {
      expect(getResponsiveNodeWidth(640)).toBe(160);
      expect(getResponsiveNodeWidth(767)).toBe(160);
    });

    it('should return 200px for desktop viewport (>= 768px)', () => {
      expect(getResponsiveNodeWidth(768)).toBe(200);
      expect(getResponsiveNodeWidth(1024)).toBe(200);
      expect(getResponsiveNodeWidth(1920)).toBe(200);
    });
  });

  describe('getLayoutConfig', () => {
    it('should return mobile config for viewport < 640px', () => {
      const config = getLayoutConfig(360);
      expect(config.nodeWidth).toBe(120);
      expect(config.levelHeight).toBe(100);
      expect(config.maxNodesPerRow).toBe(3);
    });

    it('should return tablet config for viewport 640-768px', () => {
      const config = getLayoutConfig(640);
      expect(config.nodeWidth).toBe(160);
      expect(config.levelHeight).toBe(110);
      expect(config.maxNodesPerRow).toBe(4);
    });

    it('should return desktop config for viewport >= 768px', () => {
      const config = getLayoutConfig(1024);
      expect(config.nodeWidth).toBe(200);
      expect(config.levelHeight).toBe(120);
      expect(config.maxNodesPerRow).toBe(5);
    });

    it('should include all required config properties', () => {
      const config = getLayoutConfig(1024);
      expect(config).toHaveProperty('levelHeight');
      expect(config).toHaveProperty('nodeWidth');
      expect(config).toHaveProperty('nodeHeight');
      expect(config).toHaveProperty('minSpacing');
      expect(config).toHaveProperty('maxNodesPerRow');
      expect(config).toHaveProperty('maxRowsPerLevel');
      expect(config).toHaveProperty('rowSpacing');
    });
  });

  describe('distributeNodesHorizontally', () => {
    const mockIdeas: Idea[] = [
      { id: '1', title: 'Idea 1', start_year: 2000, stage: 'Theoretical', category: 'Physics' },
      { id: '2', title: 'Idea 2', start_year: 2001, stage: 'Theoretical', category: 'Physics' },
      { id: '3', title: 'Idea 3', start_year: 2002, stage: 'Theoretical', category: 'Physics' },
    ];

    it('should distribute 3 nodes in a single row', () => {
      const config = getLayoutConfig(1024);
      const positions = distributeNodesHorizontally(mockIdeas, 1024, 100, 'ancestor', config);
      
      expect(positions).toHaveLength(3);
      expect(positions[0].level).toBe('ancestor');
      expect(positions[0].y).toBe(100);
      expect(positions[1].y).toBe(100);
      expect(positions[2].y).toBe(100);
    });

    it('should center nodes horizontally', () => {
      const config = getLayoutConfig(1024);
      const positions = distributeNodesHorizontally([mockIdeas[0]], 1024, 100, 'root', config);
      
      expect(positions).toHaveLength(1);
      // Single node should be centered at containerWidth / 2
      expect(positions[0].x).toBe(512); // 1024 / 2
    });

    it('should create multiple rows when exceeding maxNodesPerRow', () => {
      const manyIdeas: Idea[] = Array.from({ length: 7 }, (_, i) => ({
        id: `${i + 1}`,
        title: `Idea ${i + 1}`,
        start_year: 2000 + i,
        stage: 'Theoretical',
        category: 'Physics',
      }));

      const config = getLayoutConfig(1024);
      const positions = distributeNodesHorizontally(manyIdeas, 1024, 100, 'descendant', config);
      
      expect(positions).toHaveLength(7);
      
      // First 5 nodes should be in row 0
      expect(positions[0].y).toBe(100);
      expect(positions[4].y).toBe(100);
      
      // Next 2 nodes should be in row 1 (100 + 80 = 180)
      expect(positions[5].y).toBe(180);
      expect(positions[6].y).toBe(180);
    });

    it('should respect maxRowsPerLevel limit', () => {
      const manyIdeas: Idea[] = Array.from({ length: 25 }, (_, i) => ({
        id: `${i + 1}`,
        title: `Idea ${i + 1}`,
        start_year: 2000 + i,
        stage: 'Theoretical',
        category: 'Physics',
      }));

      const config = getLayoutConfig(1024);
      const positions = distributeNodesHorizontally(manyIdeas, 1024, 100, 'ancestor', config);
      
      // maxRowsPerLevel is 4, maxNodesPerRow is 5, so max 20 nodes
      expect(positions).toHaveLength(20);
    });

    it('should handle empty array', () => {
      const config = getLayoutConfig(1024);
      const positions = distributeNodesHorizontally([], 1024, 100, 'ancestor', config);
      
      expect(positions).toHaveLength(0);
    });
  });

  describe('calculateLayout', () => {
    const rootIdea: Idea = {
      id: 'root',
      title: 'Root Idea',
      start_year: 2010,
      stage: 'Experimental',
      category: 'Physics',
    };

    const ancestors: Idea[] = [
      { id: 'a1', title: 'Ancestor 1', start_year: 2005, stage: 'Theoretical', category: 'Physics' },
      { id: 'a2', title: 'Ancestor 2', start_year: 2006, stage: 'Theoretical', category: 'Physics' },
    ];

    const descendants: Idea[] = [
      { id: 'd1', title: 'Descendant 1', start_year: 2015, stage: 'Applied', category: 'Physics' },
      { id: 'd2', title: 'Descendant 2', start_year: 2016, stage: 'Applied', category: 'Physics' },
    ];

    it('should create nodes for root, ancestors, and descendants', () => {
      const { nodes, edges } = calculateLayout(rootIdea, ancestors, descendants, 1024, 600);
      
      expect(nodes).toHaveLength(5); // 1 root + 2 ancestors + 2 descendants
      
      const rootNode = nodes.find(n => n.id === 'root');
      expect(rootNode).toBeDefined();
      expect(rootNode?.isRoot).toBe(true);
      expect(rootNode?.level).toBe('root');
    });

    it('should create edges connecting ancestors to root', () => {
      const { edges } = calculateLayout(rootIdea, ancestors, descendants, 1024, 600);
      
      const ancestorEdges = edges.filter(e => e.type === 'ancestor');
      expect(ancestorEdges).toHaveLength(2);
      
      expect(ancestorEdges[0].sourceId).toBe('a1');
      expect(ancestorEdges[0].targetId).toBe('root');
      expect(ancestorEdges[1].sourceId).toBe('a2');
      expect(ancestorEdges[1].targetId).toBe('root');
    });

    it('should create edges connecting root to descendants', () => {
      const { edges } = calculateLayout(rootIdea, ancestors, descendants, 1024, 600);
      
      const descendantEdges = edges.filter(e => e.type === 'descendant');
      expect(descendantEdges).toHaveLength(2);
      
      expect(descendantEdges[0].sourceId).toBe('root');
      expect(descendantEdges[0].targetId).toBe('d1');
      expect(descendantEdges[1].sourceId).toBe('root');
      expect(descendantEdges[1].targetId).toBe('d2');
    });

    it('should position ancestors above root', () => {
      const { nodes } = calculateLayout(rootIdea, ancestors, descendants, 1024, 600);
      
      const rootNode = nodes.find(n => n.id === 'root');
      const ancestorNodes = nodes.filter(n => n.level === 'ancestor');
      
      expect(rootNode).toBeDefined();
      ancestorNodes.forEach(ancestor => {
        expect(ancestor.position.y).toBeLessThan(rootNode!.position.y);
      });
    });

    it('should position descendants below root', () => {
      const { nodes } = calculateLayout(rootIdea, ancestors, descendants, 1024, 600);
      
      const rootNode = nodes.find(n => n.id === 'root');
      const descendantNodes = nodes.filter(n => n.level === 'descendant');
      
      expect(rootNode).toBeDefined();
      descendantNodes.forEach(descendant => {
        expect(descendant.position.y).toBeGreaterThan(rootNode!.position.y);
      });
    });

    it('should handle empty ancestors array', () => {
      const { nodes, edges } = calculateLayout(rootIdea, [], descendants, 1024, 600);
      
      expect(nodes).toHaveLength(3); // 1 root + 2 descendants
      expect(edges.filter(e => e.type === 'ancestor')).toHaveLength(0);
      expect(edges.filter(e => e.type === 'descendant')).toHaveLength(2);
    });

    it('should handle empty descendants array', () => {
      const { nodes, edges } = calculateLayout(rootIdea, ancestors, [], 1024, 600);
      
      expect(nodes).toHaveLength(3); // 1 root + 2 ancestors
      expect(edges.filter(e => e.type === 'ancestor')).toHaveLength(2);
      expect(edges.filter(e => e.type === 'descendant')).toHaveLength(0);
    });

    it('should handle both empty ancestors and descendants', () => {
      const { nodes, edges } = calculateLayout(rootIdea, [], [], 1024, 600);
      
      expect(nodes).toHaveLength(1); // only root
      expect(edges).toHaveLength(0);
    });
  });

  describe('validateIdeaData', () => {
    it('should return true for valid idea', () => {
      const validIdea = {
        id: '1',
        title: 'Valid Idea',
        start_year: 2000,
        stage: 'Theoretical',
        category: 'Physics',
      };
      
      expect(validateIdeaData(validIdea)).toBe(true);
    });

    it('should return false for idea missing id', () => {
      const invalidIdea = {
        title: 'Invalid Idea',
        start_year: 2000,
      };
      
      expect(validateIdeaData(invalidIdea)).toBe(false);
    });

    it('should return false for idea missing title', () => {
      const invalidIdea = {
        id: '1',
        start_year: 2000,
      };
      
      expect(validateIdeaData(invalidIdea)).toBe(false);
    });

    it('should return false for idea missing start_year', () => {
      const invalidIdea = {
        id: '1',
        title: 'Invalid Idea',
      };
      
      expect(validateIdeaData(invalidIdea)).toBe(false);
    });

    it('should return false for null or undefined', () => {
      expect(validateIdeaData(null)).toBe(false);
      expect(validateIdeaData(undefined)).toBe(false);
    });
  });

  describe('sanitizeIdeaList', () => {
    it('should filter out invalid ideas', () => {
      const mixedIdeas = [
        { id: '1', title: 'Valid 1', start_year: 2000, stage: 'Theoretical', category: 'Physics' },
        { id: '2', title: 'Valid 2', start_year: 2001, stage: 'Theoretical', category: 'Physics' },
        { title: 'Invalid - no id', start_year: 2002 },
        { id: '3', start_year: 2003 }, // missing title
        { id: '4', title: 'Invalid - no year' },
      ];
      
      const sanitized = sanitizeIdeaList(mixedIdeas);
      
      expect(sanitized).toHaveLength(2);
      expect(sanitized[0].id).toBe('1');
      expect(sanitized[1].id).toBe('2');
    });

    it('should return empty array for all invalid ideas', () => {
      const invalidIdeas = [
        { title: 'Invalid 1' },
        { id: '2' },
        { start_year: 2000 },
      ];
      
      const sanitized = sanitizeIdeaList(invalidIdeas);
      
      expect(sanitized).toHaveLength(0);
    });

    it('should return all ideas if all are valid', () => {
      const validIdeas = [
        { id: '1', title: 'Valid 1', start_year: 2000, stage: 'Theoretical', category: 'Physics' },
        { id: '2', title: 'Valid 2', start_year: 2001, stage: 'Theoretical', category: 'Physics' },
      ];
      
      const sanitized = sanitizeIdeaList(validIdeas);
      
      expect(sanitized).toHaveLength(2);
    });

    it('should handle empty array', () => {
      const sanitized = sanitizeIdeaList([]);
      
      expect(sanitized).toHaveLength(0);
    });
  });
});
