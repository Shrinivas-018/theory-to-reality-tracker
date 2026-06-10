# Design Document: Idea Detail Tree Map

## Overview

The Idea Detail Tree Map feature enhances the IdeaDetailPanel component with an interactive hierarchical visualization that displays evolutionary relationships between ideas. The visualization replaces the current basic "Evolutionary Lineage" section with a rich, interactive tree structure showing ancestors (influences) and descendants (influenced ideas) arranged around a central root node.

### Design Goals

1. **Visual Clarity**: Present complex evolutionary relationships in an intuitive, hierarchical layout
2. **Interactivity**: Enable exploration through clickable nodes and hover effects
3. **Performance**: Render smoothly with up to 40 nodes (20 ancestors + 20 descendants)
4. **Consistency**: Maintain design system coherence with existing IdeaDetailPanel styling
5. **Accessibility**: Support keyboard navigation and screen readers

### Technology Stack

- **React 18.3.1**: Component framework
- **TypeScript 5.8.3**: Type safety
- **Tailwind CSS 3.4.17**: Styling system
- **Framer Motion 12.35.1**: Animation library
- **SVG**: Edge rendering
- **shadcn/ui**: UI component library (Badge, Skeleton)

## Architecture

### Component Hierarchy

```
IdeaDetailPanel
└── TreeMapVisualizer
    ├── TreeMapContainer (layout wrapper)
    ├── NodeLayer (ancestor/root/descendant nodes)
    │   └── IdeaNode (individual node cards)
    └── EdgeLayer (SVG relationship lines)
        └── RelationshipEdge (individual edges)
```

### Component Responsibilities

#### TreeMapVisualizer (Main Component)

**Purpose**: Orchestrates the tree visualization, manages layout calculations, and coordinates animations.

**Props Interface**:
```typescript
interface TreeMapVisualizerProps {
  rootIdea: Idea;
  ancestors: Idea[];
  descendants: Idea[];
  onNodeClick: (ideaId: string) => void;
  isLoading?: boolean;
}

interface Idea {
  id: string;
  title: string;
  start_year: number;
  end_year?: number;
  stage: string;
  category: string;
}
```

**State Management**:
```typescript
interface TreeMapState {
  nodePositions: Map<string, NodePosition>;
  hoveredNodeId: string | null;
  containerDimensions: { width: number; height: number };
}

interface NodePosition {
  x: number;
  y: number;
  level: 'ancestor' | 'root' | 'descendant';
}
```

**Responsibilities**:
- Calculate node positions using layout algorithm
- Manage hover state for interactive effects
- Coordinate fade-in animations on mount
- Handle responsive layout recalculation
- Render empty state when no relationships exist

#### IdeaNode (Node Card Component)

**Purpose**: Renders individual idea cards with appropriate styling and interaction handlers.

**Props Interface**:
```typescript
interface IdeaNodeProps {
  idea: Idea;
  position: NodePosition;
  isRoot: boolean;
  isHovered: boolean;
  onHover: (ideaId: string | null) => void;
  onClick: (ideaId: string) => void;
  animationDelay: number;
}
```

**Responsibilities**:
- Display idea title (truncated to 2 lines)
- Display start year
- Apply root node styling (gradient border) or standard styling
- Handle hover and click interactions
- Animate fade-in on mount
- Apply responsive sizing

#### RelationshipEdge (Edge Component)

**Purpose**: Renders SVG paths connecting related nodes.

**Props Interface**:
```typescript
interface RelationshipEdgeProps {
  sourcePosition: { x: number; y: number };
  targetPosition: { x: number; y: number };
  edgeType: 'ancestor' | 'descendant';
  isHighlighted: boolean;
  animationDelay: number;
}
```

**Responsibilities**:
- Calculate Bezier curve path between nodes
- Apply color based on edge type (pink for ancestors, violet for descendants)
- Animate stroke-dashoffset on mount
- Adjust opacity based on hover state

### Data Flow

```
IdeaDetailPanel (fetches data)
    ↓
    ├─ GET /api/ideas/:id/ancestors → ancestors[]
    ├─ GET /api/ideas/:id/descendants → descendants[]
    └─ Current idea → rootIdea
    ↓
TreeMapVisualizer (receives props)
    ↓
    ├─ Layout Engine calculates positions
    ├─ Filters to max 20 ancestors/descendants
    └─ Generates node and edge data structures
    ↓
    ├─ NodeLayer renders IdeaNode components
    └─ EdgeLayer renders RelationshipEdge components
    ↓
User Interaction (click/hover)
    ↓
onNodeClick callback → IdeaDetailPanel updates selected idea
```

## Components and Interfaces

### Layout Engine Algorithm

The layout engine positions nodes in a hierarchical structure with the root at the center.

#### Algorithm Specification

**Input**:
- `rootIdea`: The central node
- `ancestors`: Array of ancestor ideas (max 20, sorted by start_year)
- `descendants`: Array of descendant ideas (max 20, sorted by start_year)
- `containerWidth`: Available horizontal space

**Output**:
- `Map<ideaId, NodePosition>`: Positions for all nodes

**Algorithm Steps**:

1. **Vertical Level Assignment**:
   ```typescript
   const LEVEL_HEIGHT = 120; // pixels between levels
   const ROOT_Y = containerHeight / 2;
   
   levels = {
     ancestor: ROOT_Y - LEVEL_HEIGHT,
     root: ROOT_Y,
     descendant: ROOT_Y + LEVEL_HEIGHT
   };
   ```

2. **Horizontal Distribution**:
   ```typescript
   function distributeNodesHorizontally(
     nodes: Idea[],
     containerWidth: number,
     maxNodesPerRow: number = 5
   ): NodePosition[] {
     const NODE_WIDTH = 200; // including margins
     const MIN_SPACING = 16;
     
     const rows = Math.ceil(nodes.length / maxNodesPerRow);
     const positions: NodePosition[] = [];
     
     for (let row = 0; row < rows; row++) {
       const nodesInRow = nodes.slice(
         row * maxNodesPerRow,
         (row + 1) * maxNodesPerRow
       );
       
       const totalWidth = nodesInRow.length * NODE_WIDTH;
       const startX = (containerWidth - totalWidth) / 2;
       
       nodesInRow.forEach((node, index) => {
         positions.push({
           x: startX + index * NODE_WIDTH + NODE_WIDTH / 2,
           y: baseY + row * 80, // 80px row spacing
           level: currentLevel
         });
       });
     }
     
     return positions;
   }
   ```

3. **Multi-Row Layout**:
   - When more than 5 nodes exist at a level, arrange in multiple rows
   - Each row is centered horizontally
   - Rows are spaced 80 pixels apart vertically
   - Maximum 4 rows per level to prevent excessive height

4. **Responsive Adjustments**:
   ```typescript
   function getResponsiveNodeWidth(viewportWidth: number): number {
     if (viewportWidth < 640) return 120; // mobile
     if (viewportWidth < 768) return 160; // tablet
     return 200; // desktop
   }
   ```

### SVG Edge Rendering

Edges are rendered using SVG paths with cubic Bezier curves for visual appeal.

#### Edge Path Calculation

```typescript
function calculateEdgePath(
  source: { x: number; y: number },
  target: { x: number; y: number }
): string {
  const midY = (source.y + target.y) / 2;
  
  // Control points for smooth curve
  const cp1 = { x: source.x, y: midY };
  const cp2 = { x: target.x, y: midY };
  
  return `M ${source.x} ${source.y} 
          C ${cp1.x} ${cp1.y}, 
            ${cp2.x} ${cp2.y}, 
            ${target.x} ${target.y}`;
}
```

#### Edge Styling

```typescript
interface EdgeStyle {
  ancestor: {
    stroke: 'hsl(330, 70%, 60%)', // pink
    strokeWidth: 2,
    opacity: 0.3,
    hoverOpacity: 0.8
  },
  descendant: {
    stroke: 'hsl(270, 70%, 60%)', // violet
    strokeWidth: 2,
    opacity: 0.3,
    hoverOpacity: 0.8
  }
}
```

### Animation Specifications

#### Node Fade-In Animation

Using Framer Motion for declarative animations:

```typescript
const nodeVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: (delay: number) => ({
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.3,
      delay: delay * 0.05, // 50ms stagger
      ease: 'easeOut'
    }
  })
};

<motion.div
  variants={nodeVariants}
  initial="hidden"
  animate="visible"
  custom={nodeIndex}
>
  {/* Node content */}
</motion.div>
```

#### Edge Drawing Animation

```typescript
const edgeVariants = {
  hidden: {
    pathLength: 0,
    opacity: 0
  },
  visible: (delay: number) => ({
    pathLength: 1,
    opacity: 0.3,
    transition: {
      pathLength: { duration: 0.6, ease: 'easeInOut' },
      opacity: { duration: 0.3, delay: delay * 0.05 }
    }
  })
};

<motion.path
  variants={edgeVariants}
  initial="hidden"
  animate="visible"
  custom={edgeIndex}
  d={pathData}
/>
```

#### Hover Scale Animation

```typescript
const hoverVariants = {
  rest: { scale: 1 },
  hover: {
    scale: 1.05,
    transition: { duration: 0.2, ease: 'easeOut' }
  }
};
```

#### Transition Between Root Nodes

```typescript
const containerVariants = {
  exit: {
    opacity: 0,
    transition: { duration: 0.2 }
  },
  enter: {
    opacity: 1,
    transition: { duration: 0.3, delay: 0.2 }
  }
};
```

## Data Models

### Node Data Structure

```typescript
interface TreeNode {
  id: string;
  idea: Idea;
  position: NodePosition;
  level: 'ancestor' | 'root' | 'descendant';
  isRoot: boolean;
}

interface NodePosition {
  x: number;
  y: number;
  level: 'ancestor' | 'root' | 'descendant';
}
```

### Edge Data Structure

```typescript
interface TreeEdge {
  id: string;
  sourceId: string;
  targetId: string;
  sourcePosition: { x: number; y: number };
  targetPosition: { x: number; y: number };
  type: 'ancestor' | 'descendant';
}
```

### Layout Configuration

```typescript
interface LayoutConfig {
  levelHeight: number;        // 120px
  nodeWidth: number;          // 200px (desktop), 120px (mobile)
  nodeHeight: number;         // 80px
  minSpacing: number;         // 16px
  maxNodesPerRow: number;     // 5
  maxRowsPerLevel: number;    // 4
  rowSpacing: number;         // 80px
}
```

## Error Handling

### Loading States

```typescript
if (isLoading) {
  return (
    <div className="flex items-center justify-center p-8">
      <Skeleton className="h-96 w-full" />
    </div>
  );
}
```

### Empty State

```typescript
if (ancestors.length === 0 && descendants.length === 0) {
  return (
    <div className="bg-slate-50/50 p-6 rounded-xl border border-slate-200 text-center">
      <p className="text-sm text-slate-500 italic">
        This is an emergent standalone concept with no explicitly mapped 
        ancestors or descendants in the knowledge graph.
      </p>
    </div>
  );
}
```

### Error Boundaries

Wrap TreeMapVisualizer in an error boundary to catch rendering errors:

```typescript
class TreeMapErrorBoundary extends React.Component {
  state = { hasError: false };
  
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-center text-sm text-red-600">
          Failed to render tree visualization. Please try refreshing.
        </div>
      );
    }
    return this.props.children;
  }
}
```

### Data Validation

```typescript
function validateIdeaData(idea: any): idea is Idea {
  return (
    typeof idea?.id === 'string' &&
    typeof idea?.title === 'string' &&
    typeof idea?.start_year === 'number'
  );
}

function sanitizeIdeaList(ideas: any[]): Idea[] {
  return ideas.filter(validateIdeaData);
}
```

## Testing Strategy

This feature involves UI rendering, layout calculations, and user interactions. The testing strategy uses:

### Unit Tests (Vitest + React Testing Library)

**Layout Algorithm Tests**:
- Test horizontal distribution with various node counts (1, 3, 5, 7, 12 nodes)
- Test vertical level positioning (ancestors above, descendants below)
- Test multi-row layout when exceeding 5 nodes per level
- Test responsive width calculations for mobile/tablet/desktop
- Test edge case: empty ancestor/descendant arrays
- Test edge case: single ancestor or descendant

**Component Rendering Tests**:
- Test IdeaNode renders title and year correctly
- Test root node displays gradient border
- Test standard nodes display regular border
- Test empty state message displays when no relationships exist
- Test loading skeleton displays during data fetch

**Interaction Tests**:
- Test clicking non-root node calls onNodeClick with correct ID
- Test clicking root node does not trigger callback
- Test hover state updates correctly
- Test keyboard navigation (Tab, Enter, Space)

**Edge Path Calculation Tests**:
- Test Bezier curve path generation with various source/target positions
- Test path calculation handles negative coordinates
- Test path calculation handles coincident points

### Integration Tests

**Data Flow Tests**:
- Test TreeMapVisualizer receives and processes ancestor/descendant data
- Test node click triggers IdeaDetailPanel state update
- Test new root selection causes tree re-render with fade transition

**API Integration Tests**:
- Mock /api/ideas/:id/ancestors endpoint and verify data handling
- Mock /api/ideas/:id/descendants endpoint and verify data handling
- Test error handling when API returns 404 or 500

### Snapshot Tests

**Visual Regression**:
- Snapshot test: Tree with 3 ancestors, 1 root, 2 descendants
- Snapshot test: Tree with only ancestors (no descendants)
- Snapshot test: Tree with only descendants (no ancestors)
- Snapshot test: Empty state (no ancestors or descendants)
- Snapshot test: Mobile layout (viewport width 360px)
- Snapshot test: Desktop layout (viewport width 1024px)

### Accessibility Tests

**ARIA and Keyboard Tests**:
- Test all nodes are keyboard focusable
- Test Enter/Space key triggers node click
- Test focus ring is visible on focused nodes
- Test aria-label attributes are present and descriptive
- Test aria-current="true" on root node
- Test aria-hidden="true" on edge SVG elements
- Test role="tree" on container

### Performance Tests

**Rendering Performance**:
- Measure render time with 20 ancestors + 20 descendants (target: <100ms)
- Test animation frame rate during fade-in (target: 60fps)
- Test resize debouncing prevents excessive recalculations
- Test React.memo prevents unnecessary re-renders

### Manual Testing Checklist

- [ ] Hover effects work smoothly on all nodes
- [ ] Click navigation works for all non-root nodes
- [ ] Animations play correctly on initial render
- [ ] Transitions work when switching between ideas
- [ ] Layout adapts correctly on window resize
- [ ] Mobile layout is readable and clickable
- [ ] Colors match design system
- [ ] Text truncation works correctly for long titles
- [ ] Empty state displays appropriately

## Integration Points

### IdeaDetailPanel Integration

**Current Implementation**:
The IdeaDetailPanel currently displays a basic vertical list of ancestors and descendants with arrow icons.

**Integration Changes**:

1. **Replace Existing Section**:
   ```typescript
   // Remove current "Evolutionary Lineage" section (lines ~180-250)
   // Replace with:
   <section className="space-y-3">
     <h3 className="font-semibold text-lg flex items-center gap-2 border-b pb-1">
       <GitMerge className="h-4 w-4 text-pink-500" />
       Evolutionary Lineage
     </h3>
     <TreeMapVisualizer
       rootIdea={idea}
       ancestors={ancestors}
       descendants={descendants}
       onNodeClick={onSelectSimilar}
       isLoading={loading}
     />
   </section>
   ```

2. **Pass Existing Data**:
   - `ancestors` state (already fetched from `/api/ideas/:id/ancestors`)
   - `descendants` state (already fetched from `/api/ideas/:id/descendants`)
   - `idea` (current selected idea)
   - `onSelectSimilar` callback (already exists)

3. **No Backend Changes Required**:
   - Existing API endpoints provide all necessary data
   - Data structure matches component requirements

### File Structure

```
frontend/src/components/
├── IdeaDetailPanel.tsx (modified)
├── TreeMapVisualizer/
│   ├── index.tsx (main component)
│   ├── IdeaNode.tsx
│   ├── RelationshipEdge.tsx
│   ├── layoutEngine.ts (algorithm utilities)
│   ├── types.ts (TypeScript interfaces)
│   └── __tests__/
│       ├── TreeMapVisualizer.test.tsx
│       ├── IdeaNode.test.tsx
│       ├── layoutEngine.test.ts
│       └── snapshots/
```

### Styling Integration

**Tailwind Classes Used** (all from existing design system):
- Colors: `pink-500`, `violet-500`, `slate-50`, `slate-200`, `slate-700`
- Spacing: `p-3`, `p-6`, `gap-2`, `gap-4`, `mt-3`
- Borders: `border`, `rounded-lg`, `rounded-xl`
- Shadows: `shadow-sm`, `shadow-lg`, `shadow-pink-200/50`
- Typography: `text-sm`, `text-xs`, `font-medium`, `font-bold`

**No New CSS Required**: All styling uses existing Tailwind utilities.

## Performance Optimization

### Rendering Optimizations

1. **React.memo for Node Components**:
   ```typescript
   export const IdeaNode = React.memo<IdeaNodeProps>(({ idea, position, ... }) => {
     // Component implementation
   }, (prevProps, nextProps) => {
     return (
       prevProps.idea.id === nextProps.idea.id &&
       prevProps.isHovered === nextProps.isHovered &&
       prevProps.position.x === nextProps.position.x &&
       prevProps.position.y === nextProps.position.y
     );
   });
   ```

2. **Limit Node Count**:
   ```typescript
   const limitedAncestors = ancestors
     .sort((a, b) => b.start_year - a.start_year)
     .slice(0, 20);
   
   const limitedDescendants = descendants
     .sort((a, b) => b.start_year - a.start_year)
     .slice(0, 20);
   ```

3. **Debounced Resize Handler**:
   ```typescript
   const debouncedResize = useMemo(
     () => debounce(() => {
       setContainerDimensions({
         width: containerRef.current?.offsetWidth || 0,
         height: containerRef.current?.offsetHeight || 0
       });
     }, 150),
     []
   );
   
   useEffect(() => {
     window.addEventListener('resize', debouncedResize);
     return () => window.removeEventListener('resize', debouncedResize);
   }, [debouncedResize]);
   ```

4. **Memoized Layout Calculations**:
   ```typescript
   const nodePositions = useMemo(
     () => calculateLayout(rootIdea, limitedAncestors, limitedDescendants, containerWidth),
     [rootIdea.id, limitedAncestors, limitedDescendants, containerWidth]
   );
   ```

### Animation Performance

1. **Use CSS Transforms**: Prefer `transform: scale()` over width/height changes
2. **Use `will-change`**: Apply to animated elements
3. **Limit Concurrent Animations**: Stagger animations to reduce load
4. **Use `requestAnimationFrame`**: For custom animations

### Bundle Size

- Framer Motion is already in dependencies (no additional bundle cost)
- Component code estimated at ~15KB minified
- No additional dependencies required

## Accessibility Compliance

### Keyboard Navigation

**Tab Order**:
1. Ancestor nodes (left to right, top to bottom)
2. Root node (skipped, not focusable)
3. Descendant nodes (left to right, top to bottom)

**Keyboard Interactions**:
- `Tab`: Move focus to next node
- `Shift+Tab`: Move focus to previous node
- `Enter`: Activate focused node (navigate to idea)
- `Space`: Activate focused node (navigate to idea)
- `Escape`: Close IdeaDetailPanel (handled by Sheet component)

### Screen Reader Support

**ARIA Attributes**:
```typescript
<div role="tree" aria-label="Evolutionary lineage tree">
  <div role="treeitem" aria-label={`${idea.title}, ${idea.start_year}`}>
    {/* Node content */}
  </div>
</div>
```

**Root Node Announcement**:
```typescript
<div
  role="treeitem"
  aria-current="true"
  aria-label={`Current idea: ${idea.title}, ${idea.start_year}`}
>
```

**Edge Elements**:
```typescript
<svg aria-hidden="true">
  {/* Edge paths */}
</svg>
```

### Visual Accessibility

**Focus Indicators**:
```css
.node-card:focus {
  outline: 2px solid hsl(var(--primary));
  outline-offset: 2px;
}
```

**Color Contrast**:
- Text on white background: 4.5:1 minimum (WCAG AA)
- Pink/violet edges: Supplemented with position (not color-only)
- Hover states: Visible without color (scale + shadow)

**Motion Preferences**:
```typescript
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const animationDuration = prefersReducedMotion ? 0 : 0.3;
```

### WCAG Compliance Notes

This design addresses WCAG 2.1 Level AA requirements for:
- **1.4.3 Contrast**: Text meets minimum contrast ratios
- **2.1.1 Keyboard**: All functionality available via keyboard
- **2.4.7 Focus Visible**: Focus indicators are clearly visible
- **4.1.2 Name, Role, Value**: ARIA attributes provide semantic information

**Manual Testing Required**:
- Screen reader testing with NVDA/JAWS/VoiceOver
- Keyboard-only navigation testing
- Color blindness simulation testing
- Zoom testing (up to 200%)

## Responsive Design

### Breakpoints

```typescript
const breakpoints = {
  mobile: 360,   // min supported width
  sm: 640,       // Tailwind sm
  md: 768,       // Tailwind md
  lg: 1024       // Tailwind lg
};
```

### Layout Adaptations

**Mobile (< 640px)**:
- Node width: 120px
- Font size: 11px
- Padding: 8px
- Max title width: 100px
- Max nodes per row: 3
- Level height: 100px

**Tablet (640px - 768px)**:
- Node width: 160px
- Font size: 12px
- Padding: 10px
- Max title width: 140px
- Max nodes per row: 4
- Level height: 110px

**Desktop (> 768px)**:
- Node width: 200px
- Font size: 13px
- Padding: 12px
- Max title width: 180px
- Max nodes per row: 5
- Level height: 120px

### Responsive Implementation

```typescript
function useResponsiveLayout() {
  const [viewport, setViewport] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
  
  useEffect(() => {
    const updateViewport = () => {
      const width = window.innerWidth;
      if (width < 640) setViewport('mobile');
      else if (width < 768) setViewport('tablet');
      else setViewport('desktop');
    };
    
    updateViewport();
    window.addEventListener('resize', debounce(updateViewport, 150));
    return () => window.removeEventListener('resize', updateViewport);
  }, []);
  
  return viewport;
}
```

## Security Considerations

### XSS Prevention

**User-Generated Content**:
- Idea titles are rendered as text content (React escapes by default)
- No `dangerouslySetInnerHTML` used
- No inline event handlers in HTML strings

**Data Validation**:
```typescript
function sanitizeTitle(title: string): string {
  return title.replace(/<[^>]*>/g, '').substring(0, 200);
}
```

### API Security

- All API calls use existing authenticated endpoints
- No new security surface introduced
- CORS handled by existing backend configuration

## Future Enhancements

### Phase 2 Potential Features

1. **Zoom and Pan**: Add D3-style zoom/pan for large trees
2. **Collapsible Branches**: Allow users to collapse/expand ancestor/descendant groups
3. **Search Highlighting**: Highlight nodes matching search query
4. **Export**: Export tree as PNG or SVG
5. **Minimap**: Add overview minimap for large trees
6. **Timeline View**: Alternative view showing ideas on a timeline
7. **Filtering**: Filter nodes by category or stage
8. **Tooltips**: Show full idea details on hover without clicking

### Technical Debt Considerations

- **Layout Algorithm**: Current algorithm is simple; may need optimization for very large trees
- **Animation Performance**: Monitor frame rates on low-end devices
- **Bundle Size**: Consider lazy loading if component grows significantly
- **Browser Compatibility**: Test on older browsers (IE11 not supported)

## Deployment Considerations

### Build Configuration

No changes required to Vite configuration. Component uses standard React/TypeScript features.

### Environment Variables

No new environment variables required. Uses existing API base URL.

### Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile Browsers**: iOS Safari 14+, Chrome Android 90+
- **Not Supported**: IE11 (Framer Motion requires modern JS features)

### Performance Monitoring

Recommended metrics to track:
- Time to first render (target: <100ms)
- Animation frame rate (target: 60fps)
- Memory usage (target: <10MB for component)
- Bundle size impact (target: <20KB gzipped)

---

**Design Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Status**: Ready for Implementation
