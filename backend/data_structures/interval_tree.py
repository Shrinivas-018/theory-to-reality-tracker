"""
Interval Tree data structure for efficient time period queries.

This module implements an interval tree that allows O(log n + k) queries
for finding all intervals that overlap with a given time range, where n is
the number of intervals and k is the number of results.
"""

from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class IntervalTreeNode:
    """
    Node in the interval tree.
    
    Attributes:
        interval_start: Start of the time interval
        interval_end: End of the time interval
        max_end: Maximum end value in this subtree (for efficient pruning)
        idea_ids: List of idea IDs associated with this interval
        left: Left child node
        right: Right child node
    """
    interval_start: int
    interval_end: int
    max_end: int
    idea_ids: List[str] = field(default_factory=list)
    left: Optional['IntervalTreeNode'] = None
    right: Optional['IntervalTreeNode'] = None
    
    def __post_init__(self):
        """Validate interval constraints."""
        if self.interval_start > self.interval_end:
            raise ValueError(
                f"interval_start ({self.interval_start}) must be <= "
                f"interval_end ({self.interval_end})"
            )
        if self.max_end < self.interval_end:
            raise ValueError(
                f"max_end ({self.max_end}) must be >= "
                f"interval_end ({self.interval_end})"
            )
        if not self.idea_ids:
            raise ValueError("idea_ids must be non-empty")


class IntervalTree:
    """
    Interval tree for efficient time period overlap queries.
    
    Maintains a binary search tree on interval_start values, with each node
    storing the maximum end value in its subtree for efficient query pruning.
    """
    
    def __init__(self):
        """Initialize an empty interval tree."""
        self.root: Optional[IntervalTreeNode] = None
    
    def insert(self, start: int, end: int, idea_id: str) -> None:
        """
        Insert a new time interval into the tree.
        
        Args:
            start: Start year of the interval
            end: End year of the interval
            idea_id: ID of the idea associated with this interval
            
        Raises:
            ValueError: If start > end or years are invalid
        """
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")
        
        if start < 1800 or start > 2200 or end < 1800 or end > 2200:
            raise ValueError(
                f"Years must be between 1800 and 2200, got start={start}, end={end}"
            )
        
        self.root = self._insert_recursive(self.root, start, end, idea_id)
    
    def _insert_recursive(
        self,
        node: Optional[IntervalTreeNode],
        start: int,
        end: int,
        idea_id: str
    ) -> IntervalTreeNode:
        """
        Recursively insert interval into tree, maintaining BST property.
        
        Args:
            node: Current node in traversal
            start: Start of interval to insert
            end: End of interval to insert
            idea_id: ID to associate with interval
            
        Returns:
            Root of modified subtree
        """
        # Base case: create new node
        if node is None:
            return IntervalTreeNode(
                interval_start=start,
                interval_end=end,
                max_end=end,
                idea_ids=[idea_id]
            )
        
        # If interval matches existing node, add idea_id to it
        if node.interval_start == start and node.interval_end == end:
            if idea_id not in node.idea_ids:
                node.idea_ids.append(idea_id)
            return node
        
        # Maintain BST property: insert left or right based on start value
        if start <= node.interval_start:
            node.left = self._insert_recursive(node.left, start, end, idea_id)
        else:
            node.right = self._insert_recursive(node.right, start, end, idea_id)
        
        # Update max_end for this node
        node.max_end = max(
            node.interval_end,
            node.left.max_end if node.left else node.interval_end,
            node.right.max_end if node.right else node.interval_end
        )
        
        return node
    
    def query(self, query_start: int, query_end: int) -> List[str]:
        """
        Find all idea IDs whose time periods overlap with the query range.
        
        Time complexity: O(log n + k) where n is number of intervals,
        k is number of results.
        
        Args:
            query_start: Start of query time range
            query_end: End of query time range
            
        Returns:
            List of idea IDs with overlapping time periods
            
        Raises:
            ValueError: If query_start > query_end
        """
        if query_start > query_end:
            raise ValueError(
                f"query_start ({query_start}) must be <= query_end ({query_end})"
            )
        
        result = []
        self._query_recursive(self.root, query_start, query_end, result)
        return result
    
    def _query_recursive(
        self,
        node: Optional[IntervalTreeNode],
        query_start: int,
        query_end: int,
        result: List[str]
    ) -> None:
        """
        Recursively search tree for overlapping intervals.
        
        Args:
            node: Current node in traversal
            query_start: Start of query range
            query_end: End of query range
            result: List to accumulate matching idea IDs
        """
        # Base case: empty subtree
        if node is None:
            return
        
        # Check if current node's interval overlaps with query
        if self._intervals_overlap(
            node.interval_start, node.interval_end,
            query_start, query_end
        ):
            result.extend(node.idea_ids)
        
        # Search left subtree if it might contain overlaps
        # Left subtree can only contain overlaps if its max_end >= query_start
        if node.left is not None and node.left.max_end >= query_start:
            self._query_recursive(node.left, query_start, query_end, result)
        
        # Search right subtree if it might contain overlaps
        # Right subtree can only contain overlaps if node.interval_start <= query_end
        if node.right is not None and node.interval_start <= query_end:
            self._query_recursive(node.right, query_start, query_end, result)
    
    @staticmethod
    def _intervals_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
        """
        Check if two intervals overlap.
        
        Two intervals [start1, end1] and [start2, end2] overlap if:
        start1 <= end2 AND start2 <= end1
        
        Args:
            start1: Start of first interval
            end1: End of first interval
            start2: Start of second interval
            end2: End of second interval
            
        Returns:
            True if intervals overlap, False otherwise
        """
        return start1 <= end2 and start2 <= end1
    
    def is_empty(self) -> bool:
        """Check if the tree is empty."""
        return self.root is None
    
    def verify_invariants(self) -> bool:
        """
        Verify that tree maintains all structural invariants.
        
        Checks:
        1. BST property on interval_start
        2. max_end values are correct
        3. All nodes have valid intervals
        
        Returns:
            True if all invariants hold, False otherwise
        """
        return self._verify_recursive(self.root, float('-inf'), float('inf'))
    
    def _verify_recursive(
        self,
        node: Optional[IntervalTreeNode],
        min_start: float,
        max_start: float
    ) -> bool:
        """
        Recursively verify tree invariants.
        
        Args:
            node: Current node
            min_start: Minimum allowed interval_start (from BST property)
            max_start: Maximum allowed interval_start (from BST property)
            
        Returns:
            True if subtree maintains invariants
        """
        if node is None:
            return True
        
        # Check BST property
        if node.interval_start < min_start or node.interval_start > max_start:
            return False
        
        # Check interval validity
        if node.interval_start > node.interval_end:
            return False
        
        # Check max_end correctness
        expected_max_end = node.interval_end
        if node.left:
            expected_max_end = max(expected_max_end, node.left.max_end)
        if node.right:
            expected_max_end = max(expected_max_end, node.right.max_end)
        
        if node.max_end != expected_max_end:
            return False
        
        # Recursively check children
        left_valid = self._verify_recursive(node.left, min_start, node.interval_start)
        right_valid = self._verify_recursive(node.right, node.interval_start + 1, max_start)
        
        return left_valid and right_valid
