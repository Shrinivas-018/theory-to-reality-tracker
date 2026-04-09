"""
Segment Tree data structure for range aggregate queries over time periods.

This module implements a segment tree that allows O(log n) range queries
for counting the number of ideas active during any given time range.
Supports lazy propagation for efficient batch updates.
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass, field


@dataclass
class SegmentTreeNode:
    """
    Node in the segment tree.

    Attributes:
        range_start: Start of the year range this node covers
        range_end: End of the year range this node covers
        count: Number of ideas active in this range
        lazy: Pending lazy propagation value
        left: Left child node
        right: Right child node
    """
    range_start: int
    range_end: int
    count: int = 0
    lazy: int = 0
    left: Optional['SegmentTreeNode'] = None
    right: Optional['SegmentTreeNode'] = None

    @property
    def mid(self) -> int:
        """Midpoint of the range."""
        return (self.range_start + self.range_end) // 2

    @property
    def is_leaf(self) -> bool:
        """Check if this node is a leaf."""
        return self.range_start == self.range_end


class SegmentTree:
    """
    Segment tree for range aggregate queries on idea time periods.

    Supports:
    - Range count queries: How many ideas were active during [start, end]?
    - Point queries: How many ideas were active in year X?
    - Range updates with lazy propagation
    - Bulk construction from idea data

    Year range: 1800–2200 (configurable)
    """

    MIN_YEAR = 1800
    MAX_YEAR = 2200

    def __init__(self, min_year: int = MIN_YEAR, max_year: int = MAX_YEAR):
        """
        Initialize the segment tree.

        Args:
            min_year: Minimum year in the range
            max_year: Maximum year in the range

        Raises:
            ValueError: If min_year > max_year
        """
        if min_year > max_year:
            raise ValueError(
                f"min_year ({min_year}) must be <= max_year ({max_year})"
            )

        self.min_year = min_year
        self.max_year = max_year
        self.root = self._build(min_year, max_year)

    def _build(self, start: int, end: int) -> SegmentTreeNode:
        """
        Recursively build the segment tree.

        Args:
            start: Start of range
            end: End of range

        Returns:
            Root node of the constructed subtree
        """
        node = SegmentTreeNode(range_start=start, range_end=end)

        if start < end:
            mid = (start + end) // 2
            node.left = self._build(start, mid)
            node.right = self._build(mid + 1, end)

        return node

    def _push_down(self, node: SegmentTreeNode) -> None:
        """
        Push lazy propagation values to children.

        Args:
            node: Node whose lazy value to propagate
        """
        if node.lazy != 0 and not node.is_leaf:
            if node.left:
                node.left.count += node.lazy * (
                    node.left.range_end - node.left.range_start + 1
                )
                node.left.lazy += node.lazy
            if node.right:
                node.right.count += node.lazy * (
                    node.right.range_end - node.right.range_start + 1
                )
                node.right.lazy += node.lazy
            node.lazy = 0

    def update(self, start: int, end: int, delta: int = 1) -> None:
        """
        Update a range of years by adding delta to each year's count.

        Used to register that an idea is active during [start, end].

        Args:
            start: Start year of the range
            end: End year of the range
            delta: Value to add (default 1, use -1 to remove)

        Raises:
            ValueError: If start > end or years out of range
        """
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")

        if start < self.min_year or end > self.max_year:
            raise ValueError(
                f"Years must be between {self.min_year} and {self.max_year}, "
                f"got start={start}, end={end}"
            )

        self._update_recursive(self.root, start, end, delta)

    def _update_recursive(
        self,
        node: Optional[SegmentTreeNode],
        start: int,
        end: int,
        delta: int
    ) -> None:
        """
        Recursively update range with lazy propagation.

        Args:
            node: Current node
            start: Start of update range
            end: End of update range
            delta: Value to add
        """
        if node is None:
            return

        # No overlap
        if start > node.range_end or end < node.range_start:
            return

        # Complete overlap
        if start <= node.range_start and node.range_end <= end:
            node.count += delta * (node.range_end - node.range_start + 1)
            node.lazy += delta
            return

        # Partial overlap — push down and recurse
        self._push_down(node)
        self._update_recursive(node.left, start, end, delta)
        self._update_recursive(node.right, start, end, delta)

        # Recalculate count from children
        left_count = node.left.count if node.left else 0
        right_count = node.right.count if node.right else 0
        node.count = left_count + right_count

    def range_query(self, start: int, end: int) -> int:
        """
        Query the total count of ideas active during [start, end].

        Time complexity: O(log n)

        Args:
            start: Start year of query range
            end: End year of query range

        Returns:
            Sum of idea counts across the queried range

        Raises:
            ValueError: If start > end
        """
        if start > end:
            raise ValueError(
                f"start ({start}) must be <= end ({end})"
            )

        # Clamp to tree range
        start = max(start, self.min_year)
        end = min(end, self.max_year)

        return self._query_recursive(self.root, start, end)

    def _query_recursive(
        self,
        node: Optional[SegmentTreeNode],
        start: int,
        end: int
    ) -> int:
        """
        Recursively query range sum.

        Args:
            node: Current node
            start: Start of query range
            end: End of query range

        Returns:
            Sum of counts in the queried range
        """
        if node is None:
            return 0

        # No overlap
        if start > node.range_end or end < node.range_start:
            return 0

        # Complete overlap
        if start <= node.range_start and node.range_end <= end:
            return node.count

        # Partial overlap
        self._push_down(node)
        left_sum = self._query_recursive(node.left, start, end)
        right_sum = self._query_recursive(node.right, start, end)
        return left_sum + right_sum

    def point_query(self, year: int) -> int:
        """
        Query how many ideas are active at a specific year.

        Args:
            year: The year to query

        Returns:
            Number of ideas active at that year

        Raises:
            ValueError: If year is out of range
        """
        if year < self.min_year or year > self.max_year:
            raise ValueError(
                f"Year must be between {self.min_year} and {self.max_year}, "
                f"got {year}"
            )

        return self._point_query_recursive(self.root, year)

    def _point_query_recursive(
        self,
        node: Optional[SegmentTreeNode],
        year: int
    ) -> int:
        """
        Recursively query a single point.

        Args:
            node: Current node
            year: Year to query

        Returns:
            Count at the queried year
        """
        if node is None:
            return 0

        if node.is_leaf:
            return node.count

        self._push_down(node)

        if year <= node.mid:
            return self._point_query_recursive(node.left, year)
        else:
            return self._point_query_recursive(node.right, year)

    def build_from_ideas(
        self,
        ideas: List[Tuple[int, int, str]]
    ) -> None:
        """
        Bulk-load ideas into the segment tree.

        Args:
            ideas: List of (start_year, end_year, idea_id) tuples
        """
        for start, end, _ in ideas:
            self.update(start, end, 1)

    def get_peak_year(self) -> Tuple[int, int]:
        """
        Find the year with the maximum number of active ideas.

        Returns:
            Tuple of (year, count) for the peak year
        """
        best_year = self.min_year
        best_count = 0

        for year in range(self.min_year, self.max_year + 1):
            count = self.point_query(year)
            if count > best_count:
                best_count = count
                best_year = year

        return best_year, best_count

    def get_activity_histogram(
        self,
        start: int,
        end: int,
        bucket_size: int = 10
    ) -> List[dict]:
        """
        Get a histogram of idea activity over time.

        Args:
            start: Start year
            end: End year
            bucket_size: Size of each bucket in years

        Returns:
            List of dicts with 'period' and 'count' keys
        """
        histogram = []
        current = start

        while current <= end:
            bucket_end = min(current + bucket_size - 1, end)
            count = self.range_query(current, bucket_end)
            histogram.append({
                'period': f"{current}-{bucket_end}",
                'start': current,
                'end': bucket_end,
                'count': count
            })
            current += bucket_size

        return histogram
