~# Implementation Plan: Idea Detail Tree Map

## Overview

This implementation plan breaks down the creation of an interactive hierarchical tree map visualization for the IdeaDetailPanel component. The visualization will replace the current basic "Evolutionary Lineage" section with a rich, interactive tree structure showing ancestors (influences) and descendants (influenced ideas) arranged around a central root node. The implementation uses React 18.3.1, TypeScript 5.8.3, Framer Motion 12.35.1, and Tailwind CSS 3.4.17.

## Tasks

- [x] 1. Set up component structure and TypeScript interfaces
  - Create `frontend/src/components/TreeMapVisualizer/` directory
  - Create `types.ts` with all TypeScript interfaces (TreeMapVisualizerProps, Idea, TreeMapState, NodePosition, TreeNode, TreeEdge, LayoutConfig)
  - Create `index.tsx` as the main TreeMapVisualizer component file
  - Create `IdeaNode.tsx` for individual node card components
  - Create `RelationshipEdge.tsx` for SVG edge rendering
  - Create `layoutEngine.ts` for layout calculation utilities
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implement layout engine algorithm
  - [x] 2.1 Create layout calculation functions in `layoutEngine.ts`
    - Implement `calculateLayout()` function that takes rootIdea, ancestors, descendants, and containerWidth
    - Implement vertical level assignment logic (ancestors above, root center, descendants below)
    - Implement `distributeNodesHorizontally()` function for horizontal node distribution
    - Implement multi-row layout logic for more than 5 nodes per level
    - Implement responsive node width calculation based on viewport size
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 8.1, 8.2, 8.3, 8.4_

  - [ ]* 2.2 Write unit tests for layout engine
    - Test horizontal distribution with 1, 3, 5, 7, and 12 nodes
    - Test vertical level positioning for ancestors, root, and descendants
    - Test multi-row layout when exceeding 5 nodes per level
    - Test responsive width calculations for mobile (360px), tablet (640px), and desktop (1024px)
    - Test edge cases: empty ancestor/descendant arrays, single ancestor/descendant
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [x] 3. Implement IdeaNode component
  - [x] 3.1 Create IdeaNode component with props interface
    - Implement IdeaNodeProps interface (idea, position, isRoot, isHovered, onHover, onClick, animationDelay)
    - Render node card with white background and border for standard nodes
    - Display idea title with 2-line truncation and max-width of 180px
    - Display start year below title
    - Apply gradient border (pink to violet) for root node
    - Display stage badge for root node only
    - Apply rounded corners (0.75rem) and shadow effects
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 3.2 Add hover and click interactions
    - Implement hover state with increased shadow and border color change
    - Implement cursor pointer on hover for non-root nodes
    - Implement onClick handler that calls onNodeClick callback with idea ID
    - Disable click interaction for root node
    - Implement scale to 105% on hover with 200ms transition
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 3.3 Add Framer Motion animations
    - Implement fade-in animation from opacity 0 to 1 with scale 0.8 to 1
    - Apply staggered delay based on animationDelay prop (50ms per node)
    - Set animation duration to 300ms with easeOut easing
    - Implement hover scale animation variants
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 3.4 Implement responsive styling
    - Apply mobile styles (padding 8px, font-size 11px, max-width 100px) for viewports < 640px
    - Apply tablet styles (padding 10px, font-size 12px, max-width 140px) for viewports 640-768px
    - Apply desktop styles (padding 12px, font-size 13px, max-width 180px) for viewports > 768px
    - Ensure clickability on screens as small as 360px
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 3.5 Add accessibility attributes
    - Add tabIndex to make node keyboard focusable
    - Add aria-label with idea title and year
    - Add visible focus ring styling
    - Add onKeyDown handler for Enter and Space keys
    - Add aria-current="true" for root node
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.7_

  - [ ]* 3.6 Write unit tests for IdeaNode component
    - Test component renders title and year correctly
    - Test root node displays gradient border
    - Test standard nodes display regular border
    - Test clicking non-root node calls onNodeClick with correct ID
    - Test clicking root node does not trigger callback
    - Test hover state updates correctly
    - Test keyboard navigation (Tab, Enter, Space)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 5.3, 5.4, 12.1, 12.2, 12.3_

  - [ ]* 3.7 Write snapshot tests for IdeaNode
    - Snapshot test: Standard node (non-root)
    - Snapshot test: Root node with gradient border
    - Snapshot test: Mobile layout (360px viewport)
    - Snapshot test: Desktop layout (1024px viewport)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 8.1, 8.2, 8.3_

- [x] 4. Implement RelationshipEdge component
  - [x] 4.1 Create RelationshipEdge component with SVG path rendering
    - Implement RelationshipEdgeProps interface (sourcePosition, targetPosition, edgeType, isHighlighted, animationDelay)
    - Implement `calculateEdgePath()` function for Bezier curve calculation
    - Render SVG path element with calculated path data
    - Apply pink color (hsl(330, 70%, 60%)) for ancestor edges
    - Apply violet color (hsl(270, 70%, 60%)) for descendant edges
    - Set stroke width to 2 pixels
    - Set base opacity to 0.3, hover opacity to 0.8
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [x] 4.2 Add Framer Motion edge drawing animation
    - Implement pathLength animation from 0 to 1
    - Implement opacity animation from 0 to 0.3
    - Set pathLength animation duration to 600ms with easeInOut easing
    - Set opacity animation duration to 300ms
    - Apply staggered delay based on animationDelay prop
    - _Requirements: 7.4, 7.5_

  - [x] 4.3 Add accessibility attributes
    - Add aria-hidden="true" to SVG element
    - _Requirements: 12.5_

  - [ ]* 4.4 Write unit tests for RelationshipEdge
    - Test Bezier curve path generation with various source/target positions
    - Test path calculation handles negative coordinates
    - Test path calculation handles coincident points
    - Test ancestor edges use pink color
    - Test descendant edges use violet color
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5. Implement main TreeMapVisualizer component
  - [x] 5.1 Create TreeMapVisualizer component with state management
    - Implement TreeMapVisualizerProps interface (rootIdea, ancestors, descendants, onNodeClick, isLoading)
    - Implement TreeMapState interface (nodePositions, hoveredNodeId, containerDimensions)
    - Set up useState hooks for nodePositions, hoveredNodeId, and containerDimensions
    - Set up useRef for container element reference
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 5.2 Implement data filtering and sorting
    - Filter ancestors to maximum 20 items, sorted by start_year (most recent first)
    - Filter descendants to maximum 20 items, sorted by start_year (most recent first)
    - Validate idea data using validateIdeaData function
    - Sanitize idea lists using sanitizeIdeaList function
    - _Requirements: 11.1, 11.2_

  - [x] 5.3 Implement layout calculation and node positioning
    - Use useMemo to calculate node positions based on rootIdea, ancestors, descendants, and containerWidth
    - Call calculateLayout from layoutEngine.ts
    - Generate TreeNode data structures with positions and metadata
    - Generate TreeEdge data structures connecting root to ancestors and descendants
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 5.4 Implement responsive layout recalculation
    - Set up useEffect to measure container dimensions on mount
    - Implement debounced resize handler (150ms debounce)
    - Update containerDimensions state on resize
    - Clean up resize event listener on unmount
    - _Requirements: 8.4, 11.4_

  - [x] 5.5 Render node and edge layers
    - Render SVG container for edges with proper viewBox and dimensions
    - Map over TreeEdge array to render RelationshipEdge components
    - Render node container with proper layout styling
    - Map over TreeNode array to render IdeaNode components
    - Pass appropriate props including hover state and animation delays
    - _Requirements: 1.1, 4.1, 4.2, 4.3_

  - [x] 5.6 Implement hover state management
    - Implement onHover callback that updates hoveredNodeId state
    - Pass isHovered prop to IdeaNode components based on hoveredNodeId
    - Pass isHighlighted prop to RelationshipEdge components based on hoveredNodeId
    - _Requirements: 5.1, 4.8_

  - [x] 5.7 Implement loading and empty states
    - Render Skeleton component when isLoading is true
    - Render empty state message when both ancestors and descendants are empty
    - Use exact empty state text from requirements
    - Apply proper styling (slate-50 background, italic text, centered)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 9.4, 9.5, 9.6_

  - [x] 5.8 Add container accessibility attributes
    - Add role="tree" to container element
    - Add aria-label="Evolutionary lineage tree" to container
    - _Requirements: 12.6_

  - [x] 5.9 Implement performance optimizations
    - Wrap IdeaNode component with React.memo and custom comparison function
    - Wrap RelationshipEdge component with React.memo
    - Use useMemo for layout calculations
    - Use useMemo for debounced resize handler
    - _Requirements: 11.3, 11.4, 11.5_

  - [ ]* 5.10 Write unit tests for TreeMapVisualizer
    - Test component receives and processes ancestor/descendant data
    - Test empty state displays when no relationships exist
    - Test loading skeleton displays during data fetch
    - Test node click triggers onNodeClick callback
    - Test hover state updates correctly
    - _Requirements: 1.1, 1.2, 1.3, 6.1, 6.2, 6.3, 9.4_

  - [ ]* 5.11 Write snapshot tests for TreeMapVisualizer
    - Snapshot test: Tree with 3 ancestors, 1 root, 2 descendants
    - Snapshot test: Tree with only ancestors (no descendants)
    - Snapshot test: Tree with only descendants (no ancestors)
    - Snapshot test: Empty state (no ancestors or descendants)
    - Snapshot test: Mobile layout (viewport width 360px)
    - Snapshot test: Desktop layout (viewport width 1024px)
    - _Requirements: 2.1, 2.2, 2.3, 6.1, 6.5, 6.6, 8.1, 8.5_

- [x] 6. Integrate TreeMapVisualizer into IdeaDetailPanel
  - [x] 6.1 Import TreeMapVisualizer component
    - Add import statement for TreeMapVisualizer in IdeaDetailPanel.tsx
    - _Requirements: 1.4, 9.1, 9.2, 9.3_

  - [x] 6.2 Replace existing Evolutionary Lineage section
    - Locate the current "Evolutionary Lineage" section (around lines 180-250)
    - Remove the existing vertical list implementation with arrow icons
    - Replace with TreeMapVisualizer component
    - Keep the section header with GitMerge icon and "Evolutionary Lineage" title
    - _Requirements: 1.4, 9.1_

  - [x] 6.3 Pass props to TreeMapVisualizer
    - Pass `idea` as rootIdea prop
    - Pass `ancestors` state as ancestors prop
    - Pass `descendants` state as descendants prop
    - Pass `onSelectSimilar` callback as onNodeClick prop
    - Pass `loading` state as isLoading prop
    - _Requirements: 1.2, 1.3, 9.1, 9.2, 9.3_

  - [ ]* 6.4 Write integration tests
    - Test TreeMapVisualizer receives correct data from IdeaDetailPanel
    - Test node click triggers IdeaDetailPanel state update
    - Test new root selection causes tree re-render with fade transition
    - Mock /api/ideas/:id/ancestors endpoint and verify data handling
    - Mock /api/ideas/:id/descendants endpoint and verify data handling
    - Test error handling when API returns 404 or 500
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 7. Add error boundary for TreeMapVisualizer
  - Create TreeMapErrorBoundary class component
  - Implement getDerivedStateFromError lifecycle method
  - Render error message when hasError is true
  - Wrap TreeMapVisualizer with error boundary in IdeaDetailPanel
  - _Requirements: 9.5_

- [x] 8. Implement motion preferences support
  - Check for prefers-reduced-motion media query
  - Set animation duration to 0 when reduced motion is preferred
  - Apply to all Framer Motion animations
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 9. Checkpoint - Ensure all tests pass and verify functionality
  - Run all unit tests and ensure they pass
  - Run all snapshot tests and ensure they pass
  - Run all integration tests and ensure they pass
  - Manually test hover effects on all nodes
  - Manually test click navigation for all non-root nodes
  - Manually test animations on initial render
  - Manually test transitions when switching between ideas
  - Manually test layout adaptation on window resize
  - Manually test mobile layout (360px viewport)
  - Manually test keyboard navigation (Tab, Enter, Space)
  - Manually test screen reader announcements
  - Manually test focus indicators
  - Manually test empty state display
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Final verification and documentation
  - Verify all TypeScript types are properly defined with no `any` types
  - Verify all Tailwind classes match the design system
  - Verify no new CSS files were created (all styling uses Tailwind)
  - Verify Framer Motion animations work smoothly at 60fps
  - Verify component renders within 100ms for datasets with up to 40 nodes
  - Verify accessibility compliance (keyboard navigation, screen readers, focus indicators)
  - Verify responsive design works on mobile (360px), tablet (640px), and desktop (1024px+)
  - Add JSDoc comments to all exported functions and components
  - Update component README if needed

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- All styling uses existing Tailwind utilities - no new CSS required
- Framer Motion 12.35.1 is already installed in package.json
- No backend changes required - uses existing API endpoints
- Component integrates seamlessly with existing IdeaDetailPanel
- Performance target: <100ms render time for up to 40 nodes
- Accessibility target: WCAG 2.1 Level AA compliance
