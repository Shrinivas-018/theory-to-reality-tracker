/**
 * Unit tests for RelationshipEdge component
 */

import { describe, it, expect } from 'vitest';
import { calculateEdgePath } from '../RelationshipEdge';

describe('RelationshipEdge', () => {
  describe('calculateEdgePath', () => {
    it('should generate correct Bezier curve path for vertical connection', () => {
      const source = { x: 100, y: 50 };
      const target = { x: 100, y: 150 };
      
      const path = calculateEdgePath(source, target);
      
      // Path should start at source
      expect(path).toContain('M 100 50');
      // Path should end at target
      expect(path).toContain('100 150');
      // Path should use cubic Bezier curve (C command)
      expect(path).toContain('C');
    });

    it('should generate correct Bezier curve path for horizontal connection', () => {
      const source = { x: 50, y: 100 };
      const target = { x: 150, y: 100 };
      
      const path = calculateEdgePath(source, target);
      
      expect(path).toContain('M 50 100');
      expect(path).toContain('150 100');
      expect(path).toContain('C');
    });

    it('should generate correct Bezier curve path for diagonal connection', () => {
      const source = { x: 50, y: 50 };
      const target = { x: 150, y: 150 };
      
      const path = calculateEdgePath(source, target);
      
      expect(path).toContain('M 50 50');
      expect(path).toContain('150 150');
      expect(path).toContain('C');
    });

    it('should handle negative coordinates', () => {
      const source = { x: -50, y: -50 };
      const target = { x: 50, y: 50 };
      
      const path = calculateEdgePath(source, target);
      
      expect(path).toContain('M -50 -50');
      expect(path).toContain('50 50');
    });

    it('should handle coincident points', () => {
      const source = { x: 100, y: 100 };
      const target = { x: 100, y: 100 };
      
      const path = calculateEdgePath(source, target);
      
      expect(path).toContain('M 100 100');
      expect(path).toContain('100 100');
    });

    it('should use midpoint for control points', () => {
      const source = { x: 100, y: 50 };
      const target = { x: 200, y: 150 };
      
      const path = calculateEdgePath(source, target);
      
      const midY = (50 + 150) / 2; // 100
      
      // Control point 1 should be at (source.x, midY)
      expect(path).toContain(`C 100 ${midY}`);
      // Control point 2 should be at (target.x, midY)
      expect(path).toContain(`200 ${midY}`);
    });
  });
});
