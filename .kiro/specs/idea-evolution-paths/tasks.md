# Implementation Plan: Idea Evolution Paths

## Overview

This implementation plan breaks down the Idea Evolution Paths feature into discrete, testable tasks. The feature adds an interactive mind map visualization to the EvolutionTracker dashboard, allowing users to select start and target ideas and view animated evolution paths. The implementation uses TypeScript with React, building upon existing components and the `/api/graph/path` backend endpoint.

## Tasks

- [x] 1. Set up Evolution Paths tab infrastructure
  - Create new tab trigger in EvolutionTracker TabsList with "Paths" label and Waypoints icon
  - Add TabsContent container for Evolution Paths with proper layout structure
  - Integrate with existing tab navigation system and ensure state persistence
  - _Requirements: FR1.1, FR1.2, FR1.3, FR1.4, FR1.5_

- [ ] 2. Implement Node Selection interface
  - [ ] 2.1 Create NodeSelector component with dual search dropdowns
    - Build searchable input fields for "Start Idea (Origin)" and "Target Idea (Destination)"
    - Implement real-time filtering with case-insensitive search across title, description, and keywords
    - Add search icons and proper placeholder text
    - _Requirements: FR2.1, FR2.2, FR2.3, FR2.4, FR2.10_

  - [ ]* 2.2 Write property test for search filtering
    - **Property 4: Filter Correctness**
    - **Validates: Requirements FR2.10**

  - [ ] 2.3 Implement dropdown results display and selection
    - Create dropdown results showing idea title, year, and colored stage indicator
    - Handle click selection to close dropdown and populate selected idea badge
    - Add clear/remove functionality with × button on selected badges
    - _Requirements: FR2.5, FR2.6, FR2.7, FR2.8, FR2.9_

  - [ ]* 2.4 Write unit tests for NodeSelector component
    - Test idea filtering with various queries
    - Test selection and deselection workflows
    - Test validation of start/target combinations
    - _Requirements: FR2.1-FR2.10_

- [ ] 3. Create Path API client and data fetching
  - [ ] 3.1 Implement PathAPIClient with fetchPath method
    - Create API client for `/api/graph/path` endpoint with proper TypeScript interfaces
    - Add error handling for network failures and malformed responses
    - Implement request validation for startId and targetId parameters
    - _Requirements: FR3.4, FR6.2, FR6.7_

  - [ ]* 3.2 Write property test for path data validation
    - **Property 1: Path Validity**
    - **Validates: Requirements FR3.4**

  - [ ] 3.3 Add loading states and error handling
    - Implement loading indicator during API requests
    - Add error messages for no path found, network failures, and invalid responses
    - Create retry functionality for failed requests
    - _Requirements: FR3.5, FR3.6, FR6.1, FR6.2, FR6.4, FR6.5_

  - [ ]* 3.4 Write unit tests for API client
    - Test successful path retrieval
    - Test error handling scenarios
    - Test request parameter validation
    - _Requirements: FR3.1-FR3.7, FR6.1-FR6.7_

- [ ] 4. Checkpoint - Ensure basic data flow works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Mind Map Visualization component
  - [ ] 5.1 Create MindMapVisualization component structure
    - Build component to receive startId and targetId props
    - Implement horizontal card layout with proper spacing and scrolling
    - Add path summary display showing step count and evolution years
    - _Requirements: FR4.1, FR4.6, FR4.7_

  - [ ] 5.2 Implement node rendering with stage-based styling
    - Create vibrant node cards displaying title, stage badge, year, and description
    - Apply stage-based color coding (purple for philosophy, blue for scientific_validation, orange for engineering_application, green for modern_technology)
    - Ensure responsive card sizing for different screen widths
    - _Requirements: FR4.2, FR4.3, FR9.1, FR9.2_

  - [ ]* 5.3 Write property test for node rendering
    - **Property 3: Connection Completeness**
    - **Validates: Requirements FR4.4, FR4.5**

  - [ ] 5.4 Add staggered node animations
    - Implement entrance animations with 0.1s delay per node using Framer Motion
    - Add smooth transitions for loading and error states
    - Ensure animations maintain 60fps performance
    - _Requirements: FR4.8, FR8.3, NFR1_

  - [ ]* 5.5 Write unit tests for MindMapVisualization
    - Test path data rendering with different path lengths
    - Test loading and error state handling
    - Test responsive behavior
    - _Requirements: FR4.1-FR4.8, FR8.1-FR8.5_

- [ ] 6. Implement animated connections between nodes
  - [ ] 6.1 Create SVG connection system
    - Build SVG overlay for drawing curved paths between consecutive nodes
    - Calculate connection points based on node positions in DOM
    - Implement smooth curved paths using quadratic Bezier curves
    - _Requirements: FR4.4_

  - [ ] 6.2 Add pulsing animation effects
    - Create pulsing opacity animation for connection lines
    - Ensure animations start only after nodes are rendered
    - Add proper cleanup for animation elements
    - _Requirements: FR4.5_

  - [ ]* 6.3 Write property test for animation timing
    - **Property 6: Animation Timing**
    - **Validates: Requirements FR4.5**

  - [ ]* 6.4 Write unit tests for connection animations
    - Test SVG path creation and positioning
    - Test animation initialization and cleanup
    - Test performance with long paths
    - _Requirements: FR4.4, FR4.5_

- [ ] 7. Add interactive features and tooltips
  - [ ] 7.1 Implement hover tooltips with detailed metrics
    - Create tooltip component showing full description, keywords, category, laureates, and influence score
    - Add 200ms hover delay and proper positioning
    - Ensure tooltips work on both desktop and mobile
    - _Requirements: FR5.1, FR5.2, FR5.4, FR5.5_

  - [ ] 7.2 Add click handling for node details
    - Integrate with existing IdeaDetailPanel component
    - Handle click events to open detailed idea information
    - Ensure proper event propagation and state management
    - _Requirements: FR5.3_

  - [ ]* 7.3 Write unit tests for interactive features
    - Test tooltip display and positioning
    - Test click handling and panel integration
    - Test touch interactions on mobile
    - _Requirements: FR5.1-FR5.5_

- [ ] 8. Implement Find Evolution Path button and validation
  - [ ] 8.1 Create path request button with validation
    - Add "Find Evolution Path" button below node selection interface
    - Implement button state management (disabled when selections invalid)
    - Add validation to prevent same start/target selection
    - _Requirements: FR3.1, FR3.2, FR3.3_

  - [ ] 8.2 Add empty state and instructional content
    - Display helpful guidance when no selections are made
    - Add visual indicators and clear instructions for first-time users
    - Implement proper empty state styling
    - _Requirements: FR7.1, FR7.2, FR7.3_

  - [ ]* 8.3 Write property test for state consistency
    - **Property 5: State Consistency**
    - **Validates: Requirements FR3.1-FR3.3, FR7.1-FR7.3**

  - [ ]* 8.4 Write unit tests for button validation
    - Test button enable/disable logic
    - Test validation messages
    - Test empty state display
    - _Requirements: FR3.1-FR3.3, FR7.1-FR7.3_

- [ ] 9. Checkpoint - Ensure core functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Add performance optimizations
  - [ ] 10.1 Implement search debouncing
    - Add 300ms debounce to search input to reduce filtering operations
    - Use React.useMemo for expensive filtering computations
    - Optimize re-renders with proper dependency arrays
    - _Requirements: FR8.1, NFR1_

  - [ ] 10.2 Add virtual scrolling for long paths
    - Implement virtual scrolling for paths longer than 15 nodes
    - Add performance warning for very long paths
    - Ensure smooth horizontal scrolling experience
    - _Requirements: FR8.2, FR8.4, FR8.5_

  - [ ]* 10.3 Write performance tests
    - Test search filtering performance with large datasets
    - Test rendering performance with long paths
    - Test animation frame rates
    - _Requirements: FR8.1-FR8.5, NFR1_

- [ ] 11. Implement accessibility features
  - [ ] 11.1 Add keyboard navigation support
    - Implement tab order for search fields, button, and path nodes
    - Add keyboard shortcuts for common actions
    - Ensure focus indicators are clearly visible
    - _Requirements: FR10.1, FR10.2, FR10.3_

  - [ ] 11.2 Add screen reader support
    - Implement ARIA labels for icon-only buttons and interactive elements
    - Add live region announcements for state changes (loading, error, path found)
    - Ensure color is not the only means of conveying stage information
    - _Requirements: FR10.4, FR10.5, FR10.6_

  - [ ]* 11.3 Write accessibility tests
    - Test keyboard navigation flows
    - Test screen reader announcements
    - Test focus management
    - _Requirements: FR10.1-FR10.6_

- [ ] 12. Add responsive design and mobile support
  - [ ] 12.1 Implement responsive layout
    - Stack node selection fields vertically on screens <768px
    - Scale node cards appropriately for mobile devices
    - Ensure minimum 44px touch targets on mobile
    - _Requirements: FR9.1, FR9.2, FR9.4, FR9.5_

  - [ ] 12.2 Add touch gesture support
    - Enable horizontal scrolling with touch gestures
    - Optimize animations for mobile performance
    - Test touch interactions for tooltips and selection
    - _Requirements: FR9.3_

  - [ ]* 12.3 Write responsive design tests
    - Test layout at different screen sizes
    - Test touch interactions
    - Test mobile performance
    - _Requirements: FR9.1-FR9.5_

- [ ] 13. Integration and final wiring
  - [ ] 13.1 Integrate all components in Evolution Paths tab
    - Wire NodeSelector to MindMapVisualization with proper prop passing
    - Ensure proper error boundary handling
    - Add loading states coordination between components
    - _Requirements: FR1.1-FR1.5, FR3.1-FR3.7_

  - [ ] 13.2 Add final polish and edge case handling
    - Handle edge cases like very short paths (2 nodes)
    - Add proper cleanup for animations and event listeners
    - Ensure consistent styling with existing dashboard components
    - _Requirements: IR2.1-IR2.5, IR3.1-IR3.5_

  - [ ]* 13.3 Write integration tests
    - Test complete user workflow from selection to visualization
    - Test error recovery scenarios
    - Test tab navigation integration
    - _Requirements: FR1.1-FR1.5, FR3.1-FR3.7, FR4.1-FR4.8_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and provide opportunities for user feedback
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests ensure components work together properly
- The implementation builds incrementally, with each phase adding functionality to the previous phase
- All code should use TypeScript for type safety and follow existing project conventions
- Components should integrate seamlessly with existing shadcn/ui components and Tailwind CSS styling