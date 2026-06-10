import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import NodeSelector from '../NodeSelector';

// Mock data for testing
const mockIdeas = [
  {
    id: '1',
    title: 'Quantum Mechanics',
    description: 'Fundamental theory in physics describing nature at atomic scale',
    stage: 'philosophy',
    start_year: 1900,
    category: 'Physics',
    laureates: ['Max Planck'],
    keywords: ['quantum', 'physics', 'atomic'],
    influence_score: 0.9,
    chain: 'Physics'
  },
  {
    id: '2',
    title: 'Classical Mechanics',
    description: 'Laws of motion and forces in macroscopic world',
    stage: 'scientific_validation',
    start_year: 1687,
    category: 'Physics',
    laureates: ['Isaac Newton'],
    keywords: ['classical', 'motion', 'forces'],
    influence_score: 0.8,
    chain: 'Physics'
  },
  {
    id: '3',
    title: 'DNA Structure',
    description: 'Double helix structure of deoxyribonucleic acid',
    stage: 'modern_technology',
    start_year: 1953,
    category: 'Biology',
    laureates: ['Watson', 'Crick'],
    keywords: ['DNA', 'genetics', 'biology'],
    influence_score: 0.95,
    chain: 'Medicine'
  }
];

const mockOnPathRequest = vi.fn();

describe('NodeSelector Component', () => {
  beforeEach(() => {
    mockOnPathRequest.mockClear();
  });

  test('renders dual search fields with proper labels and placeholders', () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={false} 
      />
    );

    expect(screen.getByText('Start Idea (Origin)')).toBeInTheDocument();
    expect(screen.getByText('Target Idea (Destination)')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search starting idea...')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search destination idea...')).toBeInTheDocument();
  });

  test('filters ideas based on title search (case-insensitive)', async () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={false} 
      />
    );

    const startInput = screen.getByPlaceholderText('Search starting idea...');
    
    // Type "quantum" (lowercase) to search for "Quantum Mechanics"
    fireEvent.change(startInput, { target: { value: 'quantum' } });
    fireEvent.focus(startInput);

    await waitFor(() => {
      expect(screen.getByText('Quantum Mechanics')).toBeInTheDocument();
      expect(screen.queryByText('Classical Mechanics')).not.toBeInTheDocument();
    });
  });

  test('filters ideas based on description search', async () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={false} 
      />
    );

    const startInput = screen.getByPlaceholderText('Search starting idea...');
    
    // Search for "atomic" which appears in Quantum Mechanics description
    fireEvent.change(startInput, { target: { value: 'atomic' } });
    fireEvent.focus(startInput);

    await waitFor(() => {
      expect(screen.getByText('Quantum Mechanics')).toBeInTheDocument();
      expect(screen.queryByText('Classical Mechanics')).not.toBeInTheDocument();
    });
  });

  test('filters ideas based on keywords search', async () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={false} 
      />
    );

    const startInput = screen.getByPlaceholderText('Search starting idea...');
    
    // Search for "genetics" which appears in DNA Structure keywords
    fireEvent.change(startInput, { target: { value: 'genetics' } });
    fireEvent.focus(startInput);

    await waitFor(() => {
      expect(screen.getByText('DNA Structure')).toBeInTheDocument();
      expect(screen.queryByText('Quantum Mechanics')).not.toBeInTheDocument();
    });
  });

  test('displays search results with title, year, and stage indicator', async () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={false} 
      />
    );

    const startInput = screen.getByPlaceholderText('Search starting idea...');
    
    fireEvent.change(startInput, { target: { value: 'quantum' } });
    fireEvent.focus(startInput);

    await waitFor(() => {
      expect(screen.getByText('Quantum Mechanics')).toBeInTheDocument();
      expect(screen.getByText('1900')).toBeInTheDocument();
      // Stage indicator should be present (purple dot for philosophy stage)
      const stageIndicator = document.querySelector('.bg-purple-500');
      expect(stageIndicator).toBeInTheDocument();
    });
  });

  test('allows selection of ideas and displays selected badges', async () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={false} 
      />
    );

    const startInput = screen.getByPlaceholderText('Search starting idea...');
    
    // Search and select start idea
    fireEvent.change(startInput, { target: { value: 'quantum' } });
    fireEvent.focus(startInput);

    await waitFor(() => {
      const quantumOption = screen.getByText('Quantum Mechanics');
      fireEvent.click(quantumOption);
    });

    // Check that the selected badge appears
    await waitFor(() => {
      expect(screen.getByText('Quantum Mechanics')).toBeInTheDocument();
      expect(screen.getByText('(1900)')).toBeInTheDocument();
    });
  });

  test('prevents same idea selection for start and target', async () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={false} 
      />
    );

    const startInput = screen.getByPlaceholderText('Search starting idea...');
    const targetInput = screen.getByPlaceholderText('Search destination idea...');
    
    // Select same idea for both start and target
    fireEvent.change(startInput, { target: { value: 'quantum' } });
    fireEvent.focus(startInput);
    
    await waitFor(() => {
      const dropdownOptions = screen.getAllByText('Quantum Mechanics');
      fireEvent.click(dropdownOptions[0]); // Click the first one (in dropdown)
    });

    fireEvent.change(targetInput, { target: { value: 'quantum' } });
    fireEvent.focus(targetInput);
    
    await waitFor(() => {
      const dropdownOptions = screen.getAllByText('Quantum Mechanics');
      // Find the one in the target dropdown (not the selected badge)
      const targetDropdownOption = dropdownOptions.find(el => 
        el.closest('.absolute.top-full') !== null
      );
      if (targetDropdownOption) {
        fireEvent.click(targetDropdownOption);
      }
    });

    // Check validation message appears
    await waitFor(() => {
      expect(screen.getByText('Please select two different ideas to find an evolution path.')).toBeInTheDocument();
    });

    // Check that Find Path button is disabled
    const findButton = screen.getByText('Find Evolution Path');
    expect(findButton).toBeDisabled();
  });

  test('enables Find Path button when valid selections are made', async () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={false} 
      />
    );

    const startInput = screen.getByPlaceholderText('Search starting idea...');
    const targetInput = screen.getByPlaceholderText('Search destination idea...');
    
    // Select different ideas for start and target
    fireEvent.change(startInput, { target: { value: 'quantum' } });
    fireEvent.focus(startInput);
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Quantum Mechanics'));
    });

    fireEvent.change(targetInput, { target: { value: 'classical' } });
    fireEvent.focus(targetInput);
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Classical Mechanics'));
    });

    // Check that Find Path button is enabled
    const findButton = screen.getByText('Find Evolution Path');
    expect(findButton).not.toBeDisabled();
  });

  test('calls onPathRequest with correct IDs when Find Path is clicked', async () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={false} 
      />
    );

    const startInput = screen.getByPlaceholderText('Search starting idea...');
    const targetInput = screen.getByPlaceholderText('Search destination idea...');
    
    // Select different ideas
    fireEvent.change(startInput, { target: { value: 'quantum' } });
    fireEvent.focus(startInput);
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Quantum Mechanics'));
    });

    fireEvent.change(targetInput, { target: { value: 'classical' } });
    fireEvent.focus(targetInput);
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Classical Mechanics'));
    });

    // Click Find Path button
    const findButton = screen.getByText('Find Evolution Path');
    fireEvent.click(findButton);

    // Verify onPathRequest was called with correct IDs
    expect(mockOnPathRequest).toHaveBeenCalledWith('1', '2');
  });

  test('shows loading state when isLoading is true', () => {
    render(
      <NodeSelector 
        ideas={mockIdeas} 
        onPathRequest={mockOnPathRequest} 
        isLoading={true} 
      />
    );

    const findButton = screen.getByText('Finding path...');
    expect(findButton).toBeDisabled();
  });
});