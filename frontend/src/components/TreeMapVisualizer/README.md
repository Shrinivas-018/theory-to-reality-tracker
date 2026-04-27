# TreeMapVisualizer Component

## Overview

The TreeMapVisualizer is an interactive hierarchical tree visualization component that displays evolutionary relationships between ideas. It shows ancestors (influences) above a central root node and descendants (influenced ideas) below, creating an intuitive visual representation of idea lineage.

## Features

- **Hierarchical Layout**: Ancestors above, root at center, descendants below
- **Interactive**: Hover effects and clickable nodes for navigation
- **Responsive**: Adapts to mobile, tablet, and desktop viewports
- **Accessible**: Full keyboard navigation and screen reader support
- **Animated**: Smooth fade-in and drawing animations with Framer Motion
- **Performance Optimized**: React.memo, useMemo, and debounced resize handling
- **Motion Preferences**: Respects `prefers-reduced-motion` for accessibility
- **Error Handling**: Error boundary catches rendering errors gracefully

## Usage

```tsx
import TreeMapVisualizer from '@/components/TreeMapVisualizer';
import TreeMapErrorBoundary from '@/components/TreeMapVisualizer/TreeMapErrorBoundary';

function MyComponent() {
  const [selectedIdea, setSelectedIdea] = useState<Idea>(/* ... */);
  const [ancestors, setAncestors] = useState<Idea[]>(/* ... */);
  const [descendants, setDescendants] = useState<Idea[]>(/* ... */);
  const [loading, setLoading] = useState(false);

  return (
    <TreeMapErrorBoundary>
      <TreeMapVisualizer
        rootIdea={selectedIdea}
        ancestors={ancestors}
        descendants={descendants}
        onNodeClick={(ideaId) => setSelectedIdea(/* fetch idea by id */)}
        isLoading={loading}
      />
    </TreeMapErrorBoundary>
  );
}
```

## Props

### TreeMapVisualizerProps

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `rootIdea` | `Idea` | Yes | The central idea to display as root |
| `ancestors` | `Idea[]` | Yes | Array of ancestor ideas (influences) |
| `descendants` | `Idea[]` | Yes | Array of descendant ideas (influenced) |
| `onNodeClick` | `(ideaId: string) => void` | Yes | Callback when a non-root node is clicked |
| `isLoading` | `boolean` | No | Shows loading skeleton when true |

### Idea Interface

```typescript
interface Idea {
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
```

## Component Architecture

```
TreeMapVisualizer (Main Component)
├── TreeMapErrorBoundary (Error Handling)
├── layoutEngine.ts (Layout Calculations)
├── IdeaNode (Node Cards)
│   ├── Title and year display
│   ├── Root node gradient border
│   ├── Hover and click interactions
│   └── Framer Motion animations
├── RelationshipEdge (SVG Edges)
│   ├── Bezier curve paths
│   ├── Color coding (pink/violet)
│   └── Drawing animations
└── types.ts (TypeScript Definitions)
```

## Layout Algorithm

The layout engine positions nodes in a hierarchical structure:

1. **Vertical Levels**: 
   - Ancestors: Root Y - 120px
   - Root: Center Y
   - Descendants: Root Y + 120px

2. **Horizontal Distribution**:
   - Maximum 5 nodes per row (desktop)
   - Maximum 3 nodes per row (mobile)
   - Centered with equal spacing
   - Multi-row layout for >5 nodes

3. **Responsive Sizing**:
   - Mobile (<640px): 120px node width
   - Tablet (640-768px): 160px node width
   - Desktop (>768px): 200px node width

## Accessibility

### Keyboard Navigation

- **Tab**: Navigate between nodes
- **Shift+Tab**: Navigate backwards
- **Enter/Space**: Activate focused node
- **Escape**: Close panel (handled by parent Sheet)

### ARIA Attributes

- `role="tree"` on container
- `role="treeitem"` on each node
- `aria-label` with idea title and year
- `aria-current="true"` on root node
- `aria-hidden="true"` on decorative edges
- Visible focus rings on all focusable elements

### Motion Preferences

The component respects the `prefers-reduced-motion` media query:
- When enabled: All animations are disabled (duration: 0)
- When disabled: Full animations with staggered delays

## Performance

### Optimizations

1. **Data Limiting**: Maximum 20 ancestors and 20 descendants
2. **React.memo**: Prevents unnecessary re-renders
3. **useMemo**: Memoizes layout calculations
4. **Debounced Resize**: 150ms debounce on window resize
5. **Efficient Rendering**: SVG for edges, CSS transforms for animations

### Performance Targets

- Render time: <100ms for up to 40 nodes
- Animation frame rate: 60fps
- Bundle size: ~15KB minified
- Memory usage: <10MB

## Styling

All styling uses Tailwind CSS utilities from the existing design system:

- **Colors**: `pink-500`, `violet-500`, `slate-50`, `slate-200`, `slate-700`
- **Spacing**: `p-3`, `p-6`, `gap-2`, `gap-4`, `mt-3`
- **Borders**: `border`, `rounded-lg`, `rounded-xl`
- **Shadows**: `shadow-sm`, `shadow-lg`, `shadow-pink-200/50`
- **Typography**: `text-sm`, `text-xs`, `font-medium`, `font-bold`

No custom CSS files are required.

## Error Handling

### Error Boundary

The `TreeMapErrorBoundary` component catches rendering errors and displays a user-friendly message:

```tsx
<TreeMapErrorBoundary>
  <TreeMapVisualizer {...props} />
</TreeMapErrorBoundary>
```

### Empty State

When both ancestors and descendants are empty, displays:
> "This is an emergent standalone concept with no explicitly mapped ancestors or descendants in the knowledge graph."

### Loading State

When `isLoading={true}`, displays a skeleton loader.

## Testing

### Unit Tests

- Layout engine calculations (29 tests)
- Edge path calculations (6 tests)
- Responsive sizing
- Multi-row layouts
- Data validation

### Running Tests

```bash
npm test -- TreeMapVisualizer --run
```

All tests pass successfully (35/35).

## Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile Browsers**: iOS Safari 14+, Chrome Android 90+
- **Not Supported**: IE11 (requires modern JS features)

## Dependencies

- React 18.3.1
- TypeScript 5.8.3
- Framer Motion 12.35.1
- Tailwind CSS 3.4.17
- shadcn/ui (Badge, Skeleton)

All dependencies are already included in the project.

## Files

```
frontend/src/components/TreeMapVisualizer/
├── index.tsx                    # Main component
├── IdeaNode.tsx                 # Node card component
├── RelationshipEdge.tsx         # SVG edge component
├── TreeMapErrorBoundary.tsx     # Error boundary
├── layoutEngine.ts              # Layout calculations
├── types.ts                     # TypeScript definitions
├── README.md                    # This file
└── __tests__/
    ├── layoutEngine.test.ts     # Layout tests
    └── RelationshipEdge.test.tsx # Edge tests
```

## Integration

The component is integrated into `IdeaDetailPanel.tsx`:

```tsx
<section className="space-y-3">
  <h3 className="font-semibold text-lg flex items-center gap-2 border-b pb-1">
    <GitMerge className="h-4 w-4 text-pink-500" />
    Evolutionary Lineage
  </h3>
  <TreeMapErrorBoundary>
    <TreeMapVisualizer
      rootIdea={idea}
      ancestors={ancestors}
      descendants={descendants}
      onNodeClick={onSelectSimilar || (() => {})}
      isLoading={loading}
    />
  </TreeMapErrorBoundary>
</section>
```

## Future Enhancements

Potential features for future versions:

- Zoom and pan for large trees
- Collapsible branches
- Search highlighting
- Export as PNG/SVG
- Timeline view
- Category filtering
- Detailed tooltips

## License

Part of the Idea Evolution Tracker project.

## Version

1.0.0 - Initial release

---

**Last Updated**: 2025-01-XX  
**Status**: Production Ready
