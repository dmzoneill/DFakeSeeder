"""
DHT Routing Table Implementation

Implements Kademlia-style routing table for DHT node management.
Manages node contacts and distance calculations for efficient peer discovery.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from lib.logger import logger
from lib.util.constants import DHTConstants


@dataclass
class NodeContact:
    """DHT node contact information"""

    node_id: bytes
    ip: str
    port: int
    last_seen: float
    good_count: int = 0
    fail_count: int = 0

    @property
    def is_good(self) -> bool:
        """Check if node is considered good"""
        return self.fail_count < 3 and (time.time() - self.last_seen) < 3600

    @property
    def is_questionable(self) -> bool:
        """Check if node is questionable"""
        return self.fail_count >= 3 or (time.time() - self.last_seen) >= 3600

    def mark_good(self):
        """Mark node as responding properly"""
        self.good_count += 1
        self.fail_count = 0
        self.last_seen = time.time()

    def mark_bad(self):
        """Mark node as failing"""
        self.fail_count += 1


class KBucket:
    """K-bucket for storing node contacts"""

    def __init__(self, k: int = 8):
        """
        Initialize K-bucket

        Args:
            k: Maximum number of nodes in bucket (Kademlia K parameter)
        """
        self.k = k
        self.nodes: List[NodeContact] = []
        self.replacement_cache: List[NodeContact] = []

    def add_node(self, contact: NodeContact) -> bool:
        """
        Add node to bucket

        Args:
            contact: Node contact to add

        Returns:
            True if node was added, False if bucket is full
        """
        # Check if node already exists
        existing = self.find_node(contact.node_id)
        if existing:
            # Move to end (most recently seen)
            self.nodes.remove(existing)
            existing.mark_good()
            self.nodes.append(existing)
            return True

        # If bucket has space, add node
        if len(self.nodes) < self.k:
            self.nodes.append(contact)
            return True

        # Bucket is full - check if we can replace questionable node
        questionable = self._find_questionable_node()
        if questionable:
            self.nodes.remove(questionable)
            self.nodes.append(contact)
            return True

        # Add to replacement cache
        self.replacement_cache.append(contact)
        if len(self.replacement_cache) > self.k:
            self.replacement_cache.pop(0)

        return False

    def find_node(self, node_id: bytes) -> Optional[NodeContact]:
        """Find node by ID"""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def remove_node(self, node_id: bytes) -> bool:
        """Remove node from bucket"""
        node = self.find_node(node_id)
        if node:
            self.nodes.remove(node)

            # Try to replace with node from replacement cache
            if self.replacement_cache:
                replacement = self.replacement_cache.pop(0)
                self.nodes.append(replacement)

            return True
        return False

    def _find_questionable_node(self) -> Optional[NodeContact]:
        """Find questionable node that can be replaced"""
        for node in self.nodes:
            if node.is_questionable:
                return node
        return None

    def get_all_good_nodes(self) -> List[NodeContact]:
        """Get all good nodes in bucket"""
        return [node for node in self.nodes if node.is_good]

    def is_full(self) -> bool:
        """Check if bucket is full"""
        return len(self.nodes) >= self.k


class RoutingTable:
    """DHT Routing table implementation"""

    def __init__(self, node_id: bytes, k: int = 8):
        """
        Initialize routing table

        Args:
            node_id: Our node's 20-byte identifier
            k: K parameter for Kademlia (nodes per bucket)
        """
        self.node_id = node_id
        self.k = k
        self.buckets: List[KBucket] = []

        # Start with one bucket for the entire space
        self.buckets.append(KBucket(k))

        logger.info(
            f"DHT Routing table initialized for node {node_id.hex()[:16]}",
            extra={"class_name": self.__class__.__name__},
        )

    def add_node(self, node_id: bytes, ip: str, port: int) -> bool:
        """
        Add node to routing table

        Args:
            node_id: 20-byte node identifier
            ip: Node IP address
            port: Node port

        Returns:
            True if node was added successfully
        """
        if node_id == self.node_id:
            return False  # Don't add ourselves

        contact = NodeContact(node_id, ip, port, time.time())
        bucket_index = self._get_bucket_index(node_id)
        bucket = self.buckets[bucket_index]

        # Try to add to bucket
        if bucket.add_node(contact):
            logger.debug(
                f"Added node {node_id.hex()[:16]} to bucket {bucket_index}",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        # If bucket is full and this is our bucket, split it
        if bucket_index == len(self.buckets) - 1 and self._should_split_bucket(bucket_index):
            self._split_bucket(bucket_index)
            return self.add_node(node_id, ip, port)  # Retry after split

        return False

    def find_closest_nodes(self, target_id: bytes, count: int = 8) -> List[NodeContact]:
        """
        Find closest nodes to target ID

        Args:
            target_id: Target node ID
            count: Number of nodes to return

        Returns:
            List of closest node contacts
        """
        all_nodes = []

        # Collect all good nodes from all buckets
        for bucket in self.buckets:
            all_nodes.extend(bucket.get_all_good_nodes())

        # Sort by XOR distance to target
        all_nodes.sort(key=lambda node: self._xor_distance(node.node_id, target_id))

        return all_nodes[:count]

    def get_node_count(self) -> int:
        """Get total number of nodes in routing table"""
        return sum(len(bucket.nodes) for bucket in self.buckets)

    def get_bucket_info(self) -> List[Dict]:
        """Get information about all buckets"""
        info = []
        for i, bucket in enumerate(self.buckets):
            info.append(
                {
                    "index": i,
                    "node_count": len(bucket.nodes),
                    "good_nodes": len(bucket.get_all_good_nodes()),
                    "is_full": bucket.is_full(),
                }
            )
        return info

    def mark_node_good(self, node_id: bytes):
        """Mark node as good (responding)"""
        bucket_index = self._get_bucket_index(node_id)
        if bucket_index < len(self.buckets):
            node = self.buckets[bucket_index].find_node(node_id)
            if node:
                node.mark_good()

    def mark_node_bad(self, node_id: bytes):
        """Mark node as bad (not responding)"""
        bucket_index = self._get_bucket_index(node_id)
        if bucket_index < len(self.buckets):
            node = self.buckets[bucket_index].find_node(node_id)
            if node:
                node.mark_bad()
                # Remove if too many failures
                if node.fail_count >= DHTConstants.MAX_FAIL_COUNT:
                    self.buckets[bucket_index].remove_node(node_id)

    def cleanup_stale_nodes(self, max_age: int = 3600):
        """
        Remove stale nodes from routing table

        Args:
            max_age: Maximum age in seconds before node is considered stale
        """
        current_time = time.time()
        removed_count = 0

        for bucket in self.buckets:
            stale_nodes = [node for node in bucket.nodes if current_time - node.last_seen > max_age]
            for node in stale_nodes:
                bucket.remove_node(node.node_id)
                removed_count += 1

        if removed_count > 0:
            logger.info(
                f"Removed {removed_count} stale nodes from routing table", extra={"class_name": self.__class__.__name__}
            )

    def _get_bucket_index(self, node_id: bytes) -> int:
        """Get bucket index for node ID"""
        distance = self._xor_distance(self.node_id, node_id)

        # Find most significant bit position
        bit_length = distance.bit_length()
        bucket_index = 160 - bit_length  # 160 bits = 20 bytes

        # Ensure index is within bucket range
        return min(bucket_index, len(self.buckets) - 1)

    def _xor_distance(self, id1: bytes, id2: bytes) -> int:
        """Calculate XOR distance between two node IDs"""
        return int.from_bytes(id1, "big") ^ int.from_bytes(id2, "big")

    def _should_split_bucket(self, bucket_index: int) -> bool:
        """Check if bucket should be split"""
        # Only split if this bucket contains our node ID range
        return bucket_index == len(self.buckets) - 1 and len(self.buckets) < 160

    def _split_bucket(self, bucket_index: int):
        """Split bucket into two buckets"""
        old_bucket = self.buckets[bucket_index]
        new_bucket = KBucket(self.k)

        # Move nodes to appropriate bucket based on bit
        bit_position = 159 - bucket_index  # Which bit to check
        nodes_to_keep = []

        for node in old_bucket.nodes:
            node_int = int.from_bytes(node.node_id, "big")
            our_int = int.from_bytes(self.node_id, "big")

            # Check bit at position
            if (node_int >> bit_position) & 1 == (our_int >> bit_position) & 1:
                nodes_to_keep.append(node)
            else:
                new_bucket.nodes.append(node)

        # Update old bucket
        old_bucket.nodes = nodes_to_keep

        # Add new bucket
        self.buckets.append(new_bucket)

        logger.debug(
            f"Split bucket {bucket_index}, now have {len(self.buckets)} buckets",
            extra={"class_name": self.__class__.__name__},
        )
