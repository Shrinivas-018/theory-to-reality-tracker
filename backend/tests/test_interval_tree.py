"""
Tests for the Interval Tree data structure.

Tests cover:
- Node creation and validation
- Tree insertion and BST property maintenance
- Query operations for overlapping intervals
- max_end value propagation
- Edge cases and error handling
"""

import pytest
from backend.data_structures.interval_tree import IntervalTree, IntervalTreeNode


class TestIntervalTreeNode:
    """Tests for IntervalTreeNode class."""
    
    def test_create_valid_node(self):
        """Test creating a valid interval tree node."""
        node = IntervalTreeNode(
            interval_start=1900,
            interval_end=1950,
            max_end=1950,
            idea_ids=["idea_1"]
        )
        
        assert node.interval_start == 1900
        assert node.interval_end == 1950
        assert node.max_end == 1950
        assert node.idea_ids == ["idea_1"]
        assert node.left is None
        assert node.right is None
    
    def test_node_with_multiple_ideas(self):
        """Test node can store multiple idea IDs."""
        node = IntervalTreeNode(
            interval_start=1900,
            interval_end=1950,
            max_end=1950,
            idea_ids=["idea_1", "idea_2", "idea_3"]
        )
        
        assert len(node.idea_ids) == 3
        assert "idea_1" in node.idea_ids
        assert "idea_2" in node.idea_ids
        assert "idea_3" in node.idea_ids
    
    def test_invalid_interval_start_greater_than_end(self):
        """Test that interval_start > interval_end raises error."""
        with pytest.raises(ValueError, match="interval_start.*must be <=.*interval_end"):
            IntervalTreeNode(
                interval_start=1950,
                interval_end=1900,
                max_end=1950,
                idea_ids=["idea_1"]
            )
    
    def test_invalid_max_end_less_than_interval_end(self):
        """Test that max_end < interval_end raises error."""
        with pytest.raises(ValueError, match="max_end.*must be >=.*interval_end"):
            IntervalTreeNode(
                interval_start=1900,
                interval_end=1950,
                max_end=1940,
                idea_ids=["idea_1"]
            )
    
    def test_empty_idea_ids_raises_error(self):
        """Test that empty idea_ids list raises error."""
        with pytest.raises(ValueError, match="idea_ids must be non-empty"):
            IntervalTreeNode(
                interval_start=1900,
                interval_end=1950,
                max_end=1950,
                idea_ids=[]
            )


class TestIntervalTreeInsertion:
    """Tests for interval tree insertion operations."""
    
    def test_insert_single_interval(self):
        """Test inserting a single interval into empty tree."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        
        assert not tree.is_empty()
        assert tree.root is not None
        assert tree.root.interval_start == 1900
        assert tree.root.interval_end == 1950
        assert tree.root.max_end == 1950
        assert tree.root.idea_ids == ["idea_1"]
    
    def test_insert_multiple_intervals_maintains_bst(self):
        """Test that multiple insertions maintain BST property."""
        tree = IntervalTree()
        tree.insert(1950, 1960, "idea_2")
        tree.insert(1920, 1940, "idea_1")
        tree.insert(1970, 1990, "idea_3")
        
        # Root should be first inserted
        assert tree.root.interval_start == 1950
        
        # Left child should have smaller start
        assert tree.root.left is not None
        assert tree.root.left.interval_start == 1920
        
        # Right child should have larger start
        assert tree.root.right is not None
        assert tree.root.right.interval_start == 1970
    
    def test_insert_updates_max_end_values(self):
        """Test that max_end values are updated correctly on insertion."""
        tree = IntervalTree()
        tree.insert(1950, 1960, "idea_1")
        tree.insert(1920, 1980, "idea_2")  # Longer interval on left
        
        # Root's max_end should be updated to include left child's end
        assert tree.root.max_end == 1980
        assert tree.root.left.max_end == 1980
    
    def test_insert_same_interval_adds_idea_id(self):
        """Test inserting same interval adds to idea_ids list."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        tree.insert(1900, 1950, "idea_2")
        
        assert len(tree.root.idea_ids) == 2
        assert "idea_1" in tree.root.idea_ids
        assert "idea_2" in tree.root.idea_ids
    
    def test_insert_duplicate_idea_id_not_added_twice(self):
        """Test that duplicate idea_id is not added twice."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        tree.insert(1900, 1950, "idea_1")
        
        assert len(tree.root.idea_ids) == 1
        assert tree.root.idea_ids == ["idea_1"]
    
    def test_insert_invalid_start_greater_than_end(self):
        """Test that invalid interval raises error."""
        tree = IntervalTree()
        
        with pytest.raises(ValueError, match="start.*must be <=.*end"):
            tree.insert(1950, 1900, "idea_1")
    
    def test_insert_year_out_of_range(self):
        """Test that years outside valid range raise error."""
        tree = IntervalTree()
        
        with pytest.raises(ValueError, match="Years must be between 1800 and 2200"):
            tree.insert(1700, 1750, "idea_1")
        
        with pytest.raises(ValueError, match="Years must be between 1800 and 2200"):
            tree.insert(2250, 2300, "idea_2")


class TestIntervalTreeQuery:
    """Tests for interval tree query operations."""
    
    def test_query_empty_tree(self):
        """Test querying an empty tree returns empty list."""
        tree = IntervalTree()
        result = tree.query(1900, 1950)
        
        assert result == []
    
    def test_query_single_overlapping_interval(self):
        """Test query finds single overlapping interval."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        
        result = tree.query(1920, 1930)
        
        assert len(result) == 1
        assert "idea_1" in result
    
    def test_query_no_overlap(self):
        """Test query with no overlapping intervals returns empty."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        tree.insert(2000, 2050, "idea_2")
        
        result = tree.query(1960, 1990)
        
        assert result == []
    
    def test_query_multiple_overlapping_intervals(self):
        """Test query finds all overlapping intervals."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        tree.insert(1920, 1960, "idea_2")
        tree.insert(1940, 1980, "idea_3")
        tree.insert(2000, 2050, "idea_4")  # No overlap
        
        result = tree.query(1930, 1970)
        
        assert len(result) == 3
        assert "idea_1" in result
        assert "idea_2" in result
        assert "idea_3" in result
        assert "idea_4" not in result
    
    def test_query_complete_overlap(self):
        """Test query where interval completely contains query range."""
        tree = IntervalTree()
        tree.insert(1900, 2000, "idea_1")
        
        result = tree.query(1950, 1960)
        
        assert len(result) == 1
        assert "idea_1" in result
    
    def test_query_partial_overlap_left(self):
        """Test query with partial overlap on left side."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        
        result = tree.query(1940, 1980)
        
        assert len(result) == 1
        assert "idea_1" in result
    
    def test_query_partial_overlap_right(self):
        """Test query with partial overlap on right side."""
        tree = IntervalTree()
        tree.insert(1950, 2000, "idea_1")
        
        result = tree.query(1920, 1960)
        
        assert len(result) == 1
        assert "idea_1" in result
    
    def test_query_exact_match(self):
        """Test query that exactly matches an interval."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        
        result = tree.query(1900, 1950)
        
        assert len(result) == 1
        assert "idea_1" in result
    
    def test_query_boundary_touch_start(self):
        """Test query where intervals touch at start boundary."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        
        # Query ends exactly where interval starts
        result = tree.query(1850, 1900)
        
        assert len(result) == 1
        assert "idea_1" in result
    
    def test_query_boundary_touch_end(self):
        """Test query where intervals touch at end boundary."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        
        # Query starts exactly where interval ends
        result = tree.query(1950, 2000)
        
        assert len(result) == 1
        assert "idea_1" in result
    
    def test_query_invalid_range(self):
        """Test that invalid query range raises error."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        
        with pytest.raises(ValueError, match="query_start.*must be <=.*query_end"):
            tree.query(1950, 1900)
    
    def test_query_with_multiple_ideas_per_interval(self):
        """Test query returns all ideas from matching intervals."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        tree.insert(1900, 1950, "idea_2")
        tree.insert(1900, 1950, "idea_3")
        
        result = tree.query(1920, 1930)
        
        assert len(result) == 3
        assert "idea_1" in result
        assert "idea_2" in result
        assert "idea_3" in result


class TestIntervalTreeInvariants:
    """Tests for interval tree structural invariants."""
    
    def test_empty_tree_invariants(self):
        """Test that empty tree satisfies invariants."""
        tree = IntervalTree()
        assert tree.verify_invariants()
    
    def test_single_node_invariants(self):
        """Test that single-node tree satisfies invariants."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        
        assert tree.verify_invariants()
    
    def test_complex_tree_invariants(self):
        """Test that complex tree maintains invariants."""
        tree = IntervalTree()
        
        # Insert multiple intervals
        intervals = [
            (1950, 1960, "idea_1"),
            (1920, 1940, "idea_2"),
            (1970, 1990, "idea_3"),
            (1910, 1930, "idea_4"),
            (1960, 1980, "idea_5"),
        ]
        
        for start, end, idea_id in intervals:
            tree.insert(start, end, idea_id)
        
        assert tree.verify_invariants()
    
    def test_bst_property_maintained(self):
        """Test that BST property is maintained after insertions."""
        tree = IntervalTree()
        tree.insert(1950, 1960, "idea_1")
        tree.insert(1920, 1940, "idea_2")
        tree.insert(1970, 1990, "idea_3")
        
        # Manually verify BST property
        assert tree.root.interval_start == 1950
        assert tree.root.left.interval_start <= tree.root.interval_start
        assert tree.root.right.interval_start > tree.root.interval_start
    
    def test_max_end_propagation(self):
        """Test that max_end values propagate correctly."""
        tree = IntervalTree()
        tree.insert(1950, 1960, "idea_1")
        tree.insert(1920, 1980, "idea_2")  # Left child with larger end
        tree.insert(1970, 1975, "idea_3")  # Right child with smaller end
        
        # Root's max_end should be max of all ends in tree
        assert tree.root.max_end == 1980
        assert tree.root.left.max_end == 1980
        assert tree.root.right.max_end == 1975


class TestIntervalTreeEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_single_year_interval(self):
        """Test interval where start equals end."""
        tree = IntervalTree()
        tree.insert(1950, 1950, "idea_1")
        
        result = tree.query(1950, 1950)
        
        assert len(result) == 1
        assert "idea_1" in result
    
    def test_large_number_of_intervals(self):
        """Test tree with many intervals."""
        tree = IntervalTree()
        
        # Insert 100 intervals
        for i in range(100):
            start = 1900 + i * 2
            end = start + 10
            tree.insert(start, end, f"idea_{i}")
        
        # Query should find overlapping intervals
        result = tree.query(1950, 1970)
        
        assert len(result) > 0
        assert tree.verify_invariants()
    
    def test_overlapping_intervals_same_start(self):
        """Test multiple intervals with same start but different ends."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        tree.insert(1900, 1960, "idea_2")
        tree.insert(1900, 1940, "idea_3")
        
        result = tree.query(1920, 1930)
        
        assert len(result) == 3
    
    def test_query_entire_range(self):
        """Test query covering entire valid year range."""
        tree = IntervalTree()
        tree.insert(1900, 1950, "idea_1")
        tree.insert(2000, 2050, "idea_2")
        
        result = tree.query(1800, 2200)
        
        assert len(result) == 2
        assert "idea_1" in result
        assert "idea_2" in result
