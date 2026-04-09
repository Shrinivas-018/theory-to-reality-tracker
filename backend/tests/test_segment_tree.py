"""
Tests for the Segment Tree data structure.

Tests cover:
- Tree construction and basic properties
- Range update operations with lazy propagation
- Range queries for aggregate counts
- Point queries for single-year counts
- Bulk loading from idea data
- Histogram and peak year analysis
- Edge cases and error handling
"""

import pytest
from backend.data_structures.segment_tree import SegmentTree, SegmentTreeNode


class TestSegmentTreeConstruction:
    """Tests for segment tree construction."""

    def test_create_default_tree(self):
        """Test creating a tree with default year range."""
        tree = SegmentTree()
        assert tree.root is not None
        assert tree.min_year == 1800
        assert tree.max_year == 2200

    def test_create_custom_range_tree(self):
        """Test creating a tree with custom year range."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        assert tree.root.range_start == 1900
        assert tree.root.range_end == 2000

    def test_invalid_range_raises_error(self):
        """Test that min_year > max_year raises error."""
        with pytest.raises(ValueError, match="min_year.*must be <= max_year"):
            SegmentTree(min_year=2000, max_year=1900)

    def test_single_year_tree(self):
        """Test creating a tree with single-year range."""
        tree = SegmentTree(min_year=1950, max_year=1950)
        assert tree.root.is_leaf
        assert tree.root.count == 0

    def test_initial_counts_are_zero(self):
        """Test that all counts start at zero."""
        tree = SegmentTree(min_year=1900, max_year=1910)
        for year in range(1900, 1911):
            assert tree.point_query(year) == 0


class TestSegmentTreeUpdate:
    """Tests for segment tree update operations."""

    def test_single_range_update(self):
        """Test updating a single range."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1920, 1950)

        assert tree.point_query(1925) == 1
        assert tree.point_query(1919) == 0
        assert tree.point_query(1951) == 0

    def test_overlapping_range_updates(self):
        """Test overlapping range updates accumulate correctly."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1920, 1950)  # Idea 1
        tree.update(1930, 1960)  # Idea 2

        assert tree.point_query(1925) == 1  # Only idea 1
        assert tree.point_query(1935) == 2  # Both ideas
        assert tree.point_query(1955) == 1  # Only idea 2
        assert tree.point_query(1965) == 0  # Neither

    def test_update_with_negative_delta(self):
        """Test removing an idea with negative delta."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1920, 1950, delta=1)
        tree.update(1920, 1950, delta=-1)

        assert tree.point_query(1935) == 0

    def test_update_invalid_range(self):
        """Test that start > end raises error."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        with pytest.raises(ValueError, match="start.*must be <= end"):
            tree.update(1950, 1920)

    def test_update_out_of_range(self):
        """Test that years outside tree range raise error."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        with pytest.raises(ValueError, match="Years must be between"):
            tree.update(1800, 1850)

    def test_update_entire_range(self):
        """Test updating the entire tree range."""
        tree = SegmentTree(min_year=1900, max_year=1910)
        tree.update(1900, 1910)

        for year in range(1900, 1911):
            assert tree.point_query(year) == 1

    def test_multiple_updates_same_range(self):
        """Test multiple updates to the same range."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1950, 1960)
        tree.update(1950, 1960)
        tree.update(1950, 1960)

        assert tree.point_query(1955) == 3


class TestSegmentTreeRangeQuery:
    """Tests for range query operations."""

    def test_empty_tree_query(self):
        """Test querying an empty tree returns zero."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        assert tree.range_query(1920, 1950) == 0

    def test_range_query_single_idea(self):
        """Test range query with single idea."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1920, 1930)

        # Query exactly matching the update range
        result = tree.range_query(1920, 1930)
        assert result == 11  # 11 years, each with count 1

    def test_range_query_partial_overlap(self):
        """Test range query with partial overlap."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1920, 1940)

        # Query overlapping only half the range
        result = tree.range_query(1930, 1950)
        # Years 1930-1940 have count 1 (11 years), 1941-1950 have count 0
        assert result == 11

    def test_range_query_no_overlap(self):
        """Test range query with no overlap returns zero."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1920, 1940)

        assert tree.range_query(1950, 1960) == 0

    def test_range_query_invalid(self):
        """Test that invalid query range raises error."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        with pytest.raises(ValueError, match="start.*must be <= end"):
            tree.range_query(1950, 1920)


class TestSegmentTreePointQuery:
    """Tests for point query operations."""

    def test_point_query_active_year(self):
        """Test point query on a year with an active idea."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1920, 1950)
        assert tree.point_query(1935) == 1

    def test_point_query_inactive_year(self):
        """Test point query on a year with no active ideas."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1920, 1950)
        assert tree.point_query(1910) == 0

    def test_point_query_out_of_range(self):
        """Test point query outside tree range raises error."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        with pytest.raises(ValueError, match="Year must be between"):
            tree.point_query(1800)

    def test_point_query_boundary(self):
        """Test point query at range boundaries."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.update(1920, 1950)

        assert tree.point_query(1920) == 1  # Start boundary
        assert tree.point_query(1950) == 1  # End boundary
        assert tree.point_query(1919) == 0  # Just before
        assert tree.point_query(1951) == 0  # Just after


class TestSegmentTreeBulkLoad:
    """Tests for bulk loading ideas."""

    def test_build_from_ideas(self):
        """Test building tree from idea list."""
        tree = SegmentTree(min_year=1900, max_year=2100)
        ideas = [
            (1925, 1950, "quantum_mechanics"),
            (1950, 1970, "quantum_validation"),
            (1980, 2000, "quantum_gates"),
            (2020, 2050, "quantum_computing"),
        ]
        tree.build_from_ideas(ideas)

        assert tree.point_query(1935) == 1  # Only quantum mechanics
        assert tree.point_query(1950) == 2  # Overlap: mechanics + validation
        assert tree.point_query(1975) == 0  # Gap
        assert tree.point_query(1990) == 1  # Only gates

    def test_build_from_empty_list(self):
        """Test building from empty list produces zero-count tree."""
        tree = SegmentTree(min_year=1900, max_year=2000)
        tree.build_from_ideas([])
        assert tree.point_query(1950) == 0


class TestSegmentTreeAnalysis:
    """Tests for analysis features."""

    def test_get_activity_histogram(self):
        """Test histogram generation."""
        tree = SegmentTree(min_year=1900, max_year=1950)
        tree.update(1910, 1930)

        histogram = tree.get_activity_histogram(1900, 1950, bucket_size=10)

        assert len(histogram) == 6  # 1900-1909, 1910-1919, ..., 1950-1950
        assert histogram[0]['count'] == 0   # 1900-1909: nothing
        assert histogram[1]['count'] == 10  # 1910-1919: 10 years active
        assert histogram[2]['count'] == 10  # 1920-1929: 10 years active
        assert histogram[3]['count'] == 1   # 1930-1930 (within 1930-1939): 1 year

    def test_get_peak_year(self):
        """Test finding the peak year."""
        tree = SegmentTree(min_year=1940, max_year=1960)
        tree.update(1945, 1955)  # Idea 1
        tree.update(1948, 1958)  # Idea 2
        tree.update(1950, 1960)  # Idea 3

        year, count = tree.get_peak_year()

        # Years 1950-1955 have all 3 ideas active
        assert 1950 <= year <= 1955
        assert count == 3


class TestSegmentTreeNode:
    """Tests for SegmentTreeNode properties."""

    def test_mid_property(self):
        """Test mid-point calculation."""
        node = SegmentTreeNode(range_start=1900, range_end=2000)
        assert node.mid == 1950

    def test_is_leaf_property(self):
        """Test leaf detection."""
        leaf = SegmentTreeNode(range_start=1950, range_end=1950)
        assert leaf.is_leaf

        non_leaf = SegmentTreeNode(range_start=1900, range_end=2000)
        assert not non_leaf.is_leaf
