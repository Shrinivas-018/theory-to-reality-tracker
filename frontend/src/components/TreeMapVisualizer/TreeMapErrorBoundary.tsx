/**
 * TreeMapErrorBoundary Component
 * 
 * Error boundary that catches rendering errors in TreeMapVisualizer
 * and displays a user-friendly error message.
 * 
 * Validates: Requirements 9.5
 */

import React, { Component, ReactNode } from 'react';

interface TreeMapErrorBoundaryProps {
  children: ReactNode;
}

interface TreeMapErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

/**
 * Error boundary for TreeMapVisualizer component
 * 
 * Catches errors during rendering and displays a fallback UI
 * instead of crashing the entire application.
 */
export class TreeMapErrorBoundary extends Component<
  TreeMapErrorBoundaryProps,
  TreeMapErrorBoundaryState
> {
  constructor(props: TreeMapErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): TreeMapErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error details for debugging
    console.error('TreeMapVisualizer error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-red-50/50 p-6 rounded-xl border border-red-200 text-center">
          <p className="text-sm text-red-600">
            Failed to render tree visualization. Please try refreshing.
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}

export default TreeMapErrorBoundary;
