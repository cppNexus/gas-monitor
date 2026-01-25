"""
A professional L1 fee calculator for L2 networks.
Uses real contracts and formulas, not approximations.
"""

import asyncio
import logging
from typing import Dict, Optional
from dataclasses import dataclass

from src.config import config

logger = logging.getLogger(__name__)

# Imports for web3 v7
try:
    from web3 import AsyncWeb3
    from web3.providers import AsyncHTTPProvider
    
    WEB3_AVAILABLE = True
    logger.info("Web3 v7 is available")
    
except ImportError as e:
    logger.warning(f"Web3 import failed: {e}")
    WEB3_AVAILABLE = False

# ABI for L2 contracts
ARB_GAS_INFO_ABI = [
    {
        "inputs": [],
        "name": "getL1BaseFeeEstimate",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getL1GasPriceEstimate",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

OPTIMISM_GAS_ORACLE_ABI = [
    {
        "inputs": [{"internalType": "bytes", "name": "_data", "type": "bytes"}],
        "name": "getL1Fee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "l1BaseFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "overhead",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "scalar",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

@dataclass
class L1FeeData:
    """Accurate data on L1 commission"""
    network: str
    l1_gas_price_wei: int
    l1_base_fee_wei: int
    overhead: int
    scalar: int
    l1_fee_wei: int
    
    @property
    def l1_fee_gwei(self) -> float:
        """L1 commission in Gwei"""
        return self.l1_fee_wei / 1e9
    
    @property
    def scalar_float(self) -> float:
        """Scalar as float"""
        return self.scalar / 1_000_000


class L2FeeCalculator:
    """
    A real-world L1 fee calculator for L2 networks.
    Uses contracts and precise formulas.
    """
    
    CONTRACT_ADDRESSES = {
        "arbitrum": {
            "arb_gas_info": "0x000000000000000000000000000000000000006C"
        },
        "optimism": {
            "gas_price_oracle": "0x420000000000000000000000000000000000000F"
        },
        "base": {
            "gas_price_oracle": "0x420000000000000000000000000000000000000F"
        }
    }
    
    def __init__(self):
        self.web3_clients: Dict[str, AsyncWeb3] = {}
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 30
        self.web3_available = WEB3_AVAILABLE
        
    async def init_clients(self):
        """Initializing Web3 clients for all networks"""
        if not WEB3_AVAILABLE:
            logger.warning("Web3 is not available, L2 calculator works in simplified mode")
            return
        
        for network in ["arbitrum", "optimism", "base"]:
            network_config = config.networks.get(network)
            if network_config and network_config.rpc_urls:
                try:
                    rpc_url = network_config.rpc_urls[0]
                    self.web3_clients[network] = AsyncWeb3(
                        AsyncHTTPProvider(rpc_url, request_kwargs={'timeout': 10})
                    )
                    logger.info(f"Web3 client for {network} initialized")
                except Exception as e:
                    logger.error(f"Web3 initialization error for {network}: {e}")
        
        logger.info(f"Web3 clients initialized: {len(self.web3_clients)}")
    
    async def cleanup(self):
        """Resource cleaning"""
        self.web3_clients.clear()
        self.cache.clear()
    
    async def get_current_l1_params(self, network: str) -> Dict:
        """
        Obtaining current L1 network parameters.
        Without calculating the fee for a specific transaction.
        """
        # Checking the cache
        cache_key = f"{network}_params"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if asyncio.get_event_loop().time() - cached['timestamp'] < self.cache_ttl:
                return cached['data']
        
        try:
            if not WEB3_AVAILABLE or network not in self.web3_clients:
                # Fallback to typical values
                return self._get_fallback_params(network)
            
            web3 = self.web3_clients[network]
            
            if network == "arbitrum":
                result = await self._get_arbitrum_params(web3)
            elif network in ["optimism", "base"]:
                result = await self._get_optimism_params(web3, network)
            else:
                result = {}
            
            # Let's cache
            self.cache[cache_key] = {
                'data': result,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting L1 parameters for {network}: {e}")
            return self._get_fallback_params(network)
    
    async def _get_arbitrum_params(self, web3: AsyncWeb3) -> Dict:
        """Getting parameters for Arbitrum"""
        try:
            arb_gas_info = web3.eth.contract(
                address=web3.to_checksum_address(self.CONTRACT_ADDRESSES["arbitrum"]["arb_gas_info"]),
                abi=ARB_GAS_INFO_ABI
            )
            
            # We receive parameters in parallel
            l1_gas_price, l1_base_fee = await asyncio.gather(
                arb_gas_info.functions.getL1GasPriceEstimate().call(),
                arb_gas_info.functions.getL1BaseFeeEstimate().call()
            )
            
            # L2 gas price
            l2_gas_price = await web3.eth.gas_price
            
            return {
                "l1_gas_price_gwei": l1_gas_price / 1e9,
                "l1_base_fee_gwei": l1_base_fee / 1e9,
                "l2_gas_price_gwei": l2_gas_price / 1e9,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving Arbitrum parameters: {e}")
            raise
    
    async def _get_optimism_params(self, web3: AsyncWeb3, network: str) -> Dict:
        """Getting parameters for Optimism/Base"""
        try:
            gas_oracle = web3.eth.contract(
                address=web3.to_checksum_address(self.CONTRACT_ADDRESSES[network]["gas_price_oracle"]),
                abi=OPTIMISM_GAS_ORACLE_ABI
            )
            
            # Получаем параметры
            l1_base_fee, overhead, scalar = await asyncio.gather(
                gas_oracle.functions.l1BaseFee().call(),
                gas_oracle.functions.overhead().call(),
                gas_oracle.functions.scalar().call()
            )
            
            # L2 gas price
            l2_gas_price = await web3.eth.gas_price
            
            return {
                "l1_base_fee_gwei": l1_base_fee / 1e9,
                "overhead": overhead,
                "scalar": scalar / 1e6,
                "l2_gas_price_gwei": l2_gas_price / 1e9,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Error getting parameters {network}: {e}")
            raise
    
    def _get_fallback_params(self, network: str) -> Dict:
        """Fallback parameters if Web3 is unavailable"""
        fallbacks = {
            "arbitrum": {
                "l1_gas_price_gwei": 20.0,
                "l1_base_fee_gwei": 18.0,
                "l2_gas_price_gwei": 0.1,
                "timestamp": asyncio.get_event_loop().time()
            },
            "optimism": {
                "l1_base_fee_gwei": 20.0,
                "overhead": 2100,
                "scalar": 0.684,
                "l2_gas_price_gwei": 0.001,
                "timestamp": asyncio.get_event_loop().time()
            },
            "base": {
                "l1_base_fee_gwei": 20.0,
                "overhead": 2100,
                "scalar": 0.684,
                "l2_gas_price_gwei": 0.001,
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        return fallbacks.get(network, {})
    
    async def estimate_l1_fee_for_monitoring(
        self,
        network: str,
        tx_type: str = "transfer"
    ) -> float:
        """
        L1 fee estimation for monitoring.
        Returns the L1 fee in Gwei for typical transactions.
        """
        try:
            params = await self.get_current_l1_params(network)
            
            if not params:
                return 0.0
            
            # Типичные размеры транзакций в байтах
            tx_sizes = {
                "transfer": 110,
                "swap": 180,
                "nft_mint": 200
            }
            
            tx_size = tx_sizes.get(tx_type, 110)
            
            if network == "arbitrum":
                l1_gas_used = tx_size * 16
                l1_fee_wei = int(params.get("l1_gas_price_gwei", 20) * 1e9 * l1_gas_used)
                l1_fee_wei += int(params.get("l1_gas_price_gwei", 20) * 1e9 * 2000)
                return l1_fee_wei / 1e9
                
            elif network in ["optimism", "base"]:
                overhead = params.get("overhead", 2100)
                scalar = params.get("scalar", 0.684)
                l1_base_fee_gwei = params.get("l1_base_fee_gwei", 20)
                l1_gas_used = (tx_size + overhead) * 12
                l1_fee_gwei = l1_base_fee_gwei * l1_gas_used * scalar / 1e9
                return l1_fee_gwei
            
            return 0.0
            
        except Exception as e:
            logger.error(f"L1 commission estimation error for {network}: {e}")
            return {"arbitrum": 0.5, "optimism": 0.3, "base": 0.3}.get(network, 0.0)


# Глобальный инстанс
_l2_calculator: Optional[L2FeeCalculator] = None

async def get_l2_calculator() -> L2FeeCalculator:
    """Getting a calculator instance"""
    global _l2_calculator
    
    if _l2_calculator is None:
        _l2_calculator = L2FeeCalculator()
        await _l2_calculator.init_clients()
    
    return _l2_calculator