            z   # Requirements Document: Idea Evolution Paths

## Feature Overview

The Idea Evolution Paths feature provides an interactive mind map visualization that displays the evolutionary journey between two selected ideas. Users can select a starting idea and a target idea, then view an animated, horizontally-scrolling pipeline showing each step in the evolution with detailed metrics and visual effects.

## Functional Requirements

### FR1: Evolution Paths Tab Integration

**Priority**: High  
**Derived From**: Design Section "Components and Interfaces - Evolution Paths Tab"

**Description**: The system shall provide a new "Evolution Paths" tab in the main EvolutionTracker dashboard.

**Acceptance Criteria**:
- AC1.1: A new tab trigger labeled "Paths" appears in the TabsList alongside existing tabs (Timeline, Lineage Graph, Analysis, Predictions)
- AC1.2: The tab trigger displays a Waypoints or GitMerge icon from lucide-react
- AC1.3: Clicking the tab trigger navigates to the Evolution Paths tab content
- AC1.4: The tab content renders without errors when activated
- AC1.5: The tab maintains its state when switching between tabs

### FR2: Node Selection Interface

**Priority**: High  
**Derived From**: Design Section "Components and Interfaces - Node Selection Area"

**Description**: The system shall provide dual searchable dropdown interfaces for selecting start and target ideas.

**Acceptance Criteria**:
- AC2.1: Two search input fields are displayed: "Start Idea (Origin)" and "Target Idea (Destination)"
- AC2.2: Each search field includes a search icon indicator
- AC2.3: Typing in a search field filters the idea list in real-time
- AC2.4: Filtered results display in a dropdown below the search field
- AC2.5: Each result shows the idea title, year, and a colored stage indicator
- AC2.6: Clicking a result selects that idea and closes the dropdown
- AC2.7: Selected ideas display in a colored badge with the idea title and year
- AC2.8: Each selected idea badge includes a clear/remove button (×)
- AC2.9: Clicking the remove button deselects the idea and clears the search field
- AC2.10: The search is case-insensitive and matches against title, description, and keywords

### FR3: Path Visualization Request

**Priority**: High  
**Derived From**: Design Section "Main Algorithm/Workflow"

**Description**: The system shall fetch and display the evolution path when both start and target ideas are selected.

**Acceptance Criteria**:
- AC3.1: A "Find Evolution Path" button is displayed below the selection interface
- AC3.2: The button is disabled when either start or target idea is not selected
- AC3.3: The button is disabled when start and target ideas are the same
- AC3.4: Clicking the button triggers an API request to `/api/graph/path?from={startId}&to={targetId}`
- AC3.5: A loading indicator displays while the request is in progress
- AC3.6: The button shows "Finding path..." text during loading
- AC3.7: The request completes within 5 seconds under normal conditions

### FR4: Mind Map Visualization

**Priority**: High  
**Derived From**: Design Section "Components and Interfaces - Mind Map Visualization"

**Description**: The system shall render an animated horizontal mind map displaying the evolution path.

**Acceptance Criteria**:
- AC4.1: Path nodes are displayed as vibrant cards arranged horizontally from left to right
- AC4.2: Each node card displays: idea title, stage badge, year, and brief description
- AC4.3: Node cards are colored according to their evolution stage (purple for philosophy, blue for scientific_validation, orange for engineering_application, green for modern_technology)
- AC4.4: Nodes are connected by animated lines or curves
- AC4.5: Connections display a pulsing animation effect
- AC4.6: The visualization supports horizontal scrolling for paths longer than viewport width
- AC4.7: A summary displays above the visualization showing: "Path found: X steps" and "Y years of evolution"
- AC4.8: Each node animates into view with a staggered delay (0.1s per node)

### FR5: Interactive Node Details

**Priority**: Medium  
**Derived From**: Design Section "Components and Interfaces - Mind Map Visualization"

**Description**: The system shall provide detailed information on hover and click interactions.

**Acceptance Criteria**:
- AC5.1: Hovering over a node displays a tooltip with detailed metrics
- AC5.2: The tooltip includes: full description, keywords, category, laureates, and influence score
- AC5.3: Clicking a node opens the IdeaDetailPanel with full idea information
- AC5.4: The tooltip appears within 200ms of hover
- AC5.5: The tooltip disappears when mouse leaves the node

### FR6: Error Handling

**Priority**: High  
**Derived From**: Design Section "Error Handling"

**Description**: The system shall handle error scenarios gracefully with clear user feedback.

**Acceptance Criteria**:
- AC6.1: When no path exists, display message: "No evolution path found between these two ideas"
- AC6.2: When network request fails, display message: "Failed to fetch evolution path. Please check your connection."
- AC6.3: Error messages display in a yellow-bordered alert box
- AC6.4: A retry button appears with network errors
- AC6.5: Clicking retry triggers a new request with the same parameters
- AC6.6: Node selections remain intact after errors for easy retry
- AC6.7: Malformed API responses display generic error: "Unexpected response from server"

### FR7: Empty State Handling

**Priority**: Medium  
**Derived From**: Design Section "Error Handling"

**Description**: The system shall provide helpful guidance when no selections have been made.

**Acceptance Criteria**:
- AC7.1: When no ideas are selected, display instructional text: "Pick two ideas and discover the shortest evolution path connecting them through the lineage graph"
- AC7.2: The empty state includes visual indicators (icons or illustrations)
- AC7.3: The "Find Evolution Path" button is clearly disabled with reduced opacity

### FR8: Performance Optimization

**Priority**: Medium  
**Derived From**: Design Section "Performance Considerations"

**Description**: The system shall maintain responsive performance even with long paths.

**Acceptance Criteria**:
- AC8.1: Search filtering completes within 100ms for datasets up to 500 ideas
- AC8.2: Path visualization renders within 1 second for paths up to 20 nodes
- AC8.3: Animations maintain 60fps on modern browsers
- AC8.4: Horizontal scrolling is smooth without jank
- AC8.5: For paths longer than 15 nodes, display a warning: "Long path (X nodes) - may take time to load"

### FR9: Responsive Design

**Priority**: Medium  
**Derived From**: Design Section "Open Questions & Decisions - Mobile Responsiveness"

**Description**: The system shall adapt to different screen sizes while maintaining usability.

**Acceptance Criteria**:
- AC9.1: On screens <768px wide, node selection fields stack vertically
- AC9.2: Node cards scale down appropriately on mobile devices
- AC9.3: Horizontal scrolling works with touch gestures on mobile
- AC9.4: All interactive elements have minimum 44px touch targets on mobile
- AC9.5: Text remains readable at all supported screen sizes

### FR10: Accessibility

**Priority**: Medium  
**Derived From**: General accessibility best practices

**Description**: The system shall be accessible to users with disabilities.

**Acceptance Criteria**:
- AC10.1: All interactive elements are keyboard navigable
- AC10.2: Tab order follows logical flow (start search → target search → find button → path nodes)
- AC10.3: Focus indicators are clearly visible on all interactive elements
- AC10.4: Screen readers announce state changes (loading, error, path found)
- AC10.5: Color is not the only means of conveying information (stage badges include text labels)
- AC10.6: ARIA labels are present on icon-only buttons

## Non-Functional Requirements

### NFR1: Performance

**Description**: The system shall maintain responsive performance under normal load conditions.

**Metrics**:
- Initial tab load time: <500ms
- Path fetch time: <2 seconds (95th percentile)
- Animation frame rate: ≥60fps
- Search filter latency: <100ms

### NFR2: Reliability

**Description**: The system shall handle errors gracefully without crashing the application.

**Metrics**:
- Error recovery rate: 100% (no unhandled exceptions)
- State consistency after errors: 100%
- Successful retry rate: >90%

### NFR3: Usability

**Description**: The system shall be intuitive and easy to use without training.

**Metrics**:
- Time to complete first path visualization: <60 seconds for new users
- Error message clarity: >80% user comprehension in testing
- Task completion rate: >95%

### NFR4: Compatibility

**Description**: The system shall work across modern browsers and devices.

**Supported Platforms**:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari 14+, Chrome Android 90+)

### NFR5: Maintainability

**Description**: The code shall be well-structured and documented for future maintenance.

**Requirements**:
- TypeScript types for all components and functions
- JSDoc comments for complex functions
- Component documentation in Storybook (optional)
- Unit test coverage ≥80%

### NFR6: Security

**Description**: The system shall protect against common web vulnerabilities.

**Requirements**:
- XSS prevention through React's automatic escaping
- Input validation on all user inputs
- HTTPS for all API communication
- No sensitive data logged to console in production

## Data Requirements

### DR1: Idea Data Structure

**Description**: Ideas must contain all necessary fields for visualization.

**Required Fields**:
- `id`: string (unique identifier)
- `title`: string (display name)
- `description`: string (detailed description)
- `stage`: string (evolution stage)
- `start_year`: number (year of emergence)
- `category`: string (domain category)
- `keywords`: string[] (searchable keywords)
- `influence_score`: number (0.0 - 1.0)

**Optional Fields**:
- `end_year`: number (year of obsolescence)
- `laureates`: string[] (associated people)

### DR2: Path Data Structure

**Description**: Path responses must follow a consistent format.

**Response Format**:
```json
{
  "status": "success",
  "message": "Path found",
  "data": {
    "path": ["id1", "id2", "id3"],
    "path_details": [
      {
        "id": "id1",
        "title": "Idea 1",
        "description": "...",
        "stage": "philosophy",
        "start_year": 1900,
        "category": "Physics",
        "influence_score": 0.8,
        "keywords": ["quantum", "theory"]
      }
    ]
  }
}
```

## Integration Requirements

### IR1: Backend API Integration

**Description**: The feature shall integrate with the existing Flask backend API.

**Requirements**:
- Use existing `/api/graph/path` endpoint
- Use existing `/api/ideas` endpoint for idea list
- Maintain backward compatibility with existing API consumers
- Follow existing API response format conventions

### IR2: Frontend Component Integration

**Description**: The feature shall integrate seamlessly with the existing EvolutionTracker component.

**Requirements**:
- Use existing Tabs component from shadcn/ui
- Reuse existing IdeaDetailPanel component
- Follow existing styling conventions (Tailwind CSS classes)
- Use existing state management patterns (React hooks)
- Integrate with existing idea data loading mechanism

### IR3: Styling Integration

**Description**: The feature shall match the existing visual design system.

**Requirements**:
- Use existing color palette for stage colors
- Follow existing card and badge styling
- Use existing animation patterns from Framer Motion
- Maintain consistent spacing and typography
- Use existing icon library (lucide-react)

## Constraints

### C1: Technical Constraints

- Must use TypeScript for type safety
- Must use React 18+ features (hooks, concurrent rendering)
- Must work with existing Flask backend (no backend changes required beyond existing endpoint)
- Must use existing dependencies (no new major dependencies)

### C2: Design Constraints

- Must follow existing dashboard layout patterns
- Must use existing component library (shadcn/ui)
- Must maintain visual consistency with other tabs
- Horizontal layout is required (not vertical)

### C3: Performance Constraints

- Must render paths up to 50 nodes without significant lag
- Must support datasets up to 500 ideas without performance degradation
- Must maintain 60fps animations on devices with 4GB+ RAM

### C4: Browser Constraints

- Must support modern browsers (last 2 versions)
- Must gracefully degrade on older browsers
- Must work without JavaScript (show message: "JavaScript required")

## Assumptions

### A1: Backend Availability

- The Flask backend is running and accessible at `http://localhost:5000`
- The `/api/graph/path` endpoint returns data in the expected format
- The backend handles path-finding efficiently (responds within 2 seconds)

### A2: Data Quality

- All ideas in the database have valid stage values
- All idea IDs are unique
- Path data returned by backend is acyclic (no loops)
- Idea titles and descriptions are safe for display (no malicious content)

### A3: User Environment

- Users have modern browsers with JavaScript enabled
- Users have stable internet connection
- Users have screens at least 320px wide
- Users can scroll horizontally (mouse wheel, trackpad, or touch)

### A4: Existing Functionality

- The existing EvolutionPathFinder component can be replaced or enhanced
- The existing graph data structure supports path finding
- The existing API endpoint is performant enough for real-time queries

## Dependencies

### External Dependencies

**Frontend**:
- React 18+
- Framer Motion 10+
- lucide-react (icons)
- Radix UI (via shadcn/ui)
- Tailwind CSS

**Backend**:
- Flask 2+
- NetworkX 3+ (for graph algorithms)
- Flask-CORS (for cross-origin requests)

### Internal Dependencies

**Components**:
- EvolutionTracker (parent component)
- IdeaDetailPanel (for node details)
- Tabs components (from shadcn/ui)
- Card components (from shadcn/ui)

**Services**:
- LineageGraph service (backend)
- DataStore service (backend)

**APIs**:
- `/api/graph/path` endpoint
- `/api/ideas` endpoint

## Success Metrics

### User Engagement Metrics

- **Path Visualizations per Session**: Target ≥2 paths viewed per user session
- **Tab Activation Rate**: Target ≥30% of users activate the Paths tab
- **Interaction Rate**: Target ≥50% of users who view a path interact with nodes (hover/click)

### Performance Metrics

- **Load Time**: 95th percentile <1 second
- **Error Rate**: <5% of path requests fail
- **Animation Performance**: 95th percentile ≥55fps

### Quality Metrics

- **Bug Rate**: <2 bugs per 100 user sessions
- **User Satisfaction**: ≥4.0/5.0 rating (if feedback collected)
- **Task Completion Rate**: ≥90% of users successfully visualize a path

## Future Enhancements

### FE1: Auto-Suggest Target

**Description**: Automatically suggest the most influential descendant when only start idea is selected.

**Priority**: Low  
**Effort**: Medium

### FE2: Path Comparison

**Description**: Allow users to compare multiple paths side-by-side.

**Priority**: Low  
**Effort**: High

### FE3: Export Path

**Description**: Export path visualization as image or PDF.

**Priority**: Low  
**Effort**: Medium

### FE4: Path Filtering

**Description**: Filter paths by stage, category, or time period.

**Priority**: Low  
**Effort**: Medium

### FE5: Alternative Paths

**Description**: Show multiple paths between the same start and target ideas.

**Priority**: Medium  
**Effort**: High

### FE6: Path Statistics

**Description**: Display aggregate statistics about the path (average influence, stage distribution, etc.).

**Priority**: Low  
**Effort**: Low

## Glossary

- **Evolution Path**: A sequence of ideas connected by influence relationships, showing how one idea evolved into another
- **Mind Map**: A visual representation of connected concepts, in this case showing the evolution journey
- **Node**: A single idea in the evolution path visualization
- **Stage**: The evolution stage of an idea (philosophy, scientific_validation, engineering_application, modern_technology)
- **Influence Score**: A numeric value (0.0-1.0) representing the impact or importance of an idea
- **Pipeline**: The horizontal visual layout showing the sequential flow of ideas
- **Lineage Graph**: The underlying directed graph structure representing all idea relationships
