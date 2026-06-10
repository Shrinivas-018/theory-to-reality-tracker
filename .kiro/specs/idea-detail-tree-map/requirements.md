# Requirements Document

## Introduction

This document specifies requirements for enhancing the IdeaDetailPanel component with an interactive evolution tree map visualization. The enhancement replaces the current basic "Evolutionary Lineage" section with a rich, interactive tree structure that displays the selected idea as a root node with its ancestors (influences) and descendants (influenced ideas) in a hierarchical, visually appealing layout. The visualization will enable users to explore idea relationships through an intuitive, clickable interface that maintains consistency with the existing design system.

## Glossary

- **IdeaDetailPanel**: The React component that displays detailed information about a selected idea in a right sidebar
- **Tree_Map_Visualizer**: The new component responsible for rendering the interactive evolution tree structure
- **Root_Node**: The currently selected idea displayed at the center of the tree visualization
- **Ancestor_Node**: An idea that influenced the Root_Node (parent in the evolution chain)
- **Descendant_Node**: An idea that was influenced by the Root_Node (child in the evolution chain)
- **Relationship_Edge**: A visual connection line between nodes representing influence relationships
- **Node_Card**: A clickable visual element representing a single idea in the tree
- **Layout_Engine**: The algorithm responsible for positioning nodes in the tree structure
- **API_Client**: The service that fetches ancestor and descendant data from backend endpoints

## Requirements

### Requirement 1: Tree Map Component Creation

**User Story:** As a developer, I want a dedicated tree map visualization component, so that the evolutionary lineage can be displayed in a modular and maintainable way.

#### Acceptance Criteria

1. THE Tree_Map_Visualizer SHALL be implemented as a separate React component
2. THE Tree_Map_Visualizer SHALL accept the Root_Node, Ancestor_Node list, and Descendant_Node list as props
3. THE Tree_Map_Visualizer SHALL accept an onNodeClick callback function as a prop
4. THE Tree_Map_Visualizer SHALL render within the existing IdeaDetailPanel layout without breaking the Sheet component structure
5. THE Tree_Map_Visualizer SHALL use TypeScript with proper type definitions for all props and internal state

### Requirement 2: Hierarchical Node Layout

**User Story:** As a user, I want to see ideas arranged in a clear hierarchical structure, so that I can understand the evolution chain at a glance.

#### Acceptance Criteria

1. THE Layout_Engine SHALL position the Root_Node at the center of the visualization
2. WHEN Ancestor_Node items exist, THE Layout_Engine SHALL position them above the Root_Node
3. WHEN Descendant_Node items exist, THE Layout_Engine SHALL position them below the Root_Node
4. THE Layout_Engine SHALL distribute multiple nodes at the same level horizontally with equal spacing
5. WHEN more than 5 nodes exist at a single level, THE Layout_Engine SHALL arrange them in multiple rows to prevent overcrowding
6. THE Layout_Engine SHALL maintain a minimum spacing of 16 pixels between adjacent Node_Card elements
7. THE Layout_Engine SHALL calculate positions to fit within the available container width

### Requirement 3: Visual Node Representation

**User Story:** As a user, I want each idea to be displayed as a visually distinct card, so that I can easily identify and differentiate between ideas.

#### Acceptance Criteria

1. THE Node_Card SHALL display the idea title with a maximum of 2 lines using text truncation
2. THE Node_Card SHALL display the start year below the title
3. THE Node_Card SHALL use a white background with a border for standard nodes
4. THE Root_Node SHALL use a gradient border (pink to violet) to distinguish it from other nodes
5. THE Node_Card SHALL display a stage badge for the Root_Node
6. THE Node_Card SHALL have rounded corners matching the design system (border-radius: 0.75rem)
7. THE Node_Card SHALL have a shadow effect (shadow-sm for standard nodes, shadow-lg for Root_Node)
8. THE Node_Card SHALL limit title width to 180 pixels maximum to maintain consistent card sizes

### Requirement 4: Relationship Edge Rendering

**User Story:** As a user, I want to see visual connections between related ideas, so that I can understand the influence relationships.

#### Acceptance Criteria

1. THE Tree_Map_Visualizer SHALL render Relationship_Edge elements connecting the Root_Node to each Ancestor_Node
2. THE Tree_Map_Visualizer SHALL render Relationship_Edge elements connecting the Root_Node to each Descendant_Node
3. THE Relationship_Edge SHALL be rendered as an SVG path or line element
4. THE Relationship_Edge connecting to Ancestor_Node items SHALL use a pink color (hsl(330, 70%, 60%))
5. THE Relationship_Edge connecting to Descendant_Node items SHALL use a violet color (hsl(270, 70%, 60%))
6. THE Relationship_Edge SHALL have a stroke width of 2 pixels
7. THE Relationship_Edge SHALL use a curved path (Bezier curve) rather than straight lines for visual appeal
8. WHEN an Ancestor_Node or Descendant_Node is hovered, THE corresponding Relationship_Edge SHALL increase opacity from 0.3 to 0.8

### Requirement 5: Interactive Node Behavior

**User Story:** As a user, I want to click on any node in the tree, so that I can navigate to that idea's detail view.

#### Acceptance Criteria

1. WHEN a user hovers over a Node_Card, THE Node_Card SHALL display a hover state with increased shadow and border color change
2. WHEN a user hovers over a Node_Card, THE cursor SHALL change to pointer
3. WHEN a user clicks on a Node_Card, THE Tree_Map_Visualizer SHALL invoke the onNodeClick callback with the clicked idea's ID
4. THE Root_Node SHALL not be clickable (no hover effect or cursor change)
5. WHEN a Node_Card is hovered, THE Node_Card SHALL scale to 105% of its original size with a smooth transition
6. THE hover transition SHALL complete within 200 milliseconds

### Requirement 6: Empty State Handling

**User Story:** As a user, I want to see a meaningful message when an idea has no ancestors or descendants, so that I understand the idea is standalone.

#### Acceptance Criteria

1. WHEN both Ancestor_Node list and Descendant_Node list are empty, THE Tree_Map_Visualizer SHALL display an empty state message
2. THE empty state message SHALL read "This is an emergent standalone concept with no explicitly mapped ancestors or descendants in the knowledge graph"
3. THE empty state SHALL be displayed in a centered container with a light background (slate-50)
4. THE empty state SHALL use italic text styling
5. WHEN only Ancestor_Node list is empty, THE Tree_Map_Visualizer SHALL display only the Root_Node and Descendant_Node items
6. WHEN only Descendant_Node list is empty, THE Tree_Map_Visualizer SHALL display only the Root_Node and Ancestor_Node items

### Requirement 7: Animation and Transitions

**User Story:** As a user, I want smooth animations when the tree appears, so that the interface feels polished and professional.

#### Acceptance Criteria

1. WHEN the Tree_Map_Visualizer first renders, THE Node_Card elements SHALL fade in with an opacity transition from 0 to 1
2. THE fade-in animation SHALL have a staggered delay of 50 milliseconds per node
3. THE fade-in animation SHALL complete within 300 milliseconds per node
4. WHEN the Tree_Map_Visualizer first renders, THE Relationship_Edge elements SHALL animate their stroke-dashoffset to create a drawing effect
5. THE edge drawing animation SHALL complete within 600 milliseconds
6. WHEN a new Root_Node is selected, THE Tree_Map_Visualizer SHALL fade out old nodes before fading in new nodes

### Requirement 8: Responsive Layout Adaptation

**User Story:** As a user, I want the tree map to adapt to different screen sizes, so that I can view it on mobile and desktop devices.

#### Acceptance Criteria

1. WHEN the viewport width is less than 640 pixels, THE Tree_Map_Visualizer SHALL reduce Node_Card padding to 8 pixels
2. WHEN the viewport width is less than 640 pixels, THE Tree_Map_Visualizer SHALL reduce Node_Card title font size to 11 pixels
3. WHEN the viewport width is less than 640 pixels, THE Tree_Map_Visualizer SHALL reduce maximum title width to 100 pixels
4. THE Tree_Map_Visualizer SHALL use CSS flexbox or grid for layout to enable automatic wrapping
5. THE Tree_Map_Visualizer SHALL maintain readability and clickability of all nodes on screens as small as 360 pixels wide

### Requirement 9: Integration with Existing Data Flow

**User Story:** As a developer, I want the tree map to use existing API data, so that no backend changes are required.

#### Acceptance Criteria

1. THE Tree_Map_Visualizer SHALL receive ancestor data from the existing /api/ideas/:id/ancestors endpoint
2. THE Tree_Map_Visualizer SHALL receive descendant data from the existing /api/ideas/:id/descendants endpoint
3. THE IdeaDetailPanel SHALL pass the fetched ancestors and descendants arrays to the Tree_Map_Visualizer
4. THE Tree_Map_Visualizer SHALL handle loading states by displaying a skeleton loader or spinner
5. THE Tree_Map_Visualizer SHALL handle error states by displaying an error message
6. WHEN API_Client returns an empty array, THE Tree_Map_Visualizer SHALL treat it as a valid empty state

### Requirement 10: Design System Consistency

**User Story:** As a user, I want the tree map to match the existing application design, so that the interface feels cohesive.

#### Acceptance Criteria

1. THE Tree_Map_Visualizer SHALL use Tailwind CSS utility classes for all styling
2. THE Tree_Map_Visualizer SHALL use color values from the existing design system (pink-500, violet-500, slate-50, etc.)
3. THE Tree_Map_Visualizer SHALL use the Badge component from shadcn/ui for displaying metadata
4. THE Tree_Map_Visualizer SHALL use the same font family and weights as the rest of the IdeaDetailPanel
5. THE Tree_Map_Visualizer SHALL use the same border radius values as existing Card components (0.75rem)
6. THE Tree_Map_Visualizer SHALL use spacing values that are multiples of 4 pixels (Tailwind's spacing scale)

### Requirement 11: Performance Optimization

**User Story:** As a user, I want the tree map to render quickly even with many nodes, so that the interface remains responsive.

#### Acceptance Criteria

1. WHEN more than 20 Ancestor_Node items exist, THE Tree_Map_Visualizer SHALL display only the 20 most recent ancestors by start_year
2. WHEN more than 20 Descendant_Node items exist, THE Tree_Map_Visualizer SHALL display only the 20 most recent descendants by start_year
3. THE Tree_Map_Visualizer SHALL use React.memo to prevent unnecessary re-renders
4. THE Tree_Map_Visualizer SHALL debounce window resize events to recalculate layout at most once per 150 milliseconds
5. THE Tree_Map_Visualizer SHALL render within 100 milliseconds for datasets with up to 20 nodes per level

### Requirement 12: Accessibility Compliance

**User Story:** As a user with accessibility needs, I want the tree map to be keyboard navigable and screen reader friendly, so that I can use it effectively.

#### Acceptance Criteria

1. THE Node_Card SHALL be keyboard focusable using the tab key
2. WHEN a Node_Card has focus, THE Node_Card SHALL display a visible focus ring
3. WHEN a focused Node_Card receives an Enter or Space key press, THE Tree_Map_Visualizer SHALL invoke the onNodeClick callback
4. THE Node_Card SHALL have an aria-label attribute describing the idea title and year
5. THE Relationship_Edge SHALL have an aria-hidden attribute set to true
6. THE Tree_Map_Visualizer container SHALL have a role attribute set to "tree"
7. THE Root_Node SHALL have an aria-current attribute set to "true"
