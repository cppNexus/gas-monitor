"""
Data Models for Gas Monitor.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class GasData:
    """Gas data for one network"""
    network: str
    timestamp: float
    block_number: int
    
    # Prices in Gwei
    base_fee: float
    priority_fees: Dict[str, float]  # percentile -> priority
    total_fees: Dict[str, float]     # percentile -> total (base + priority)
    
    # Additional information
    l1_fee: Optional[float] = None  # Only for L2
    l2_fee: Optional[float] = None  # Only for L2
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "network": self.network,
            "timestamp": self.timestamp,
            "block_number": self.block_number,
            "base_fee": self.base_fee,
            "priority_fees": self.priority_fees,
            "total_fees": self.total_fees,
            "l1_fee": self.l1_fee,
            "l2_fee": self.l2_fee
        }
    
    def get_fee_for_percentile(self, percentile: str) -> Optional[float]:
        """Receive total commission for a percentile"""
        return self.total_fees.get(percentile)
    
    def get_priority_for_percentile(self, percentile: str) -> Optional[float]:
        """Earning a percentile priority commission"""
        return self.priority_fees.get(percentile)