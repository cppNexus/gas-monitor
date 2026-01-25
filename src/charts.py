"""
Module for generating graphs with gas prices.
"""

import asyncio
import os
import glob
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

import matplotlib
matplotlib.use('Agg')  # For work without GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from src.config import config
from src.models import GasData

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Graph generator"""
    
    def __init__(self):
        self.chart_dir = "charts"
        self.ensure_chart_dir()
        
        # Chart styles
        self.styles = {
            "ethereum": {"color": "#627eea", "name": "Ethereum"},
            "arbitrum": {"color": "#28a0f0", "name": "Arbitrum"},
            "optimism": {"color": "#ff0420", "name": "Optimism"},
            "base": {"color": "#0052ff", "name": "Base"},
            "polygon": {"color": "#8247e5", "name": "Polygon"}
        }
    
    def ensure_chart_dir(self):
        """Creating a directory for graphs"""
        os.makedirs(self.chart_dir, exist_ok=True)
    
    async def generate_network_chart(self, 
                                   network: str, 
                                   history: List[GasData]) -> Optional[str]:
        """
        Generate a graph for a specific network.
        Returns the file path or None on error.
        """
        try:
            if not history:
                logger.warning(f"No data for graph {network}")
                return None
            
            # Preparing the data
            timestamps = []
            base_fees = []
            safe_fees = []  # p25
            fast_fees = []  # p75
            
            for data in history:
                timestamps.append(datetime.fromtimestamp(data.timestamp))
                base_fees.append(data.base_fee)
                
                safe = data.get_fee_for_percentile("p25")
                fast = data.get_fee_for_percentile("p75")
                
                if safe is not None:
                    safe_fees.append(safe)
                if fast is not None:
                    fast_fees.append(fast)
            
            # Create a schedule
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # Chart 1: Basic and Total Fees
            ax1.plot(timestamps, base_fees, 
                    label="Base Fee", 
                    color='blue', 
                    linewidth=2,
                    alpha=0.8)
            
            if safe_fees and len(safe_fees) == len(timestamps):
                ax1.plot(timestamps, safe_fees,
                        label="Safe (25%)",
                        color='green',
                        linewidth=1.5,
                        linestyle='--',
                        alpha=0.7)
            
            if fast_fees and len(fast_fees) == len(timestamps):
                ax1.plot(timestamps, fast_fees,
                        label="Fast (75%)",
                        color='red',
                        linewidth=1.5,
                        linestyle='--',
                        alpha=0.7)
            
            # Filling the space between safe and fast
            if safe_fees and fast_fees and len(safe_fees) == len(fast_fees):
                ax1.fill_between(timestamps, safe_fees, fast_fees,
                               color='orange', alpha=0.2,
                               label="Safe-Fast Range")
            
            network_config = config.networks.get(network)
            network_name = network_config.name if network_config else network
            
            ax1.set_title(f"{network_name} Gas Prices (Last {config.monitoring['max_history_hours']}h)", 
                         fontsize=16, fontweight='bold', pad=20)
            ax1.set_ylabel("Gwei", fontsize=12)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # Time formatting
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Chart 2: Priority Commissions
            if safe_fees and base_fees and len(safe_fees) == len(base_fees):
                priority_safe = [s - b for s, b in zip(safe_fees, base_fees)]
                ax2.plot(timestamps, priority_safe,
                        label="Priority (25%)",
                        color='green',
                        linewidth=1.5,
                        alpha=0.7)
            
            if fast_fees and base_fees and len(fast_fees) == len(base_fees):
                priority_fast = [f - b for f, b in zip(fast_fees, base_fees)]
                ax2.plot(timestamps, priority_fast,
                        label="Priority (75%)",
                        color='red',
                        linewidth=1.5,
                        alpha=0.7)
            
            ax2.set_title("Priority Fees", fontsize=14, pad=15)
            ax2.set_ylabel("Gwei", fontsize=12)
            ax2.set_xlabel("Time", fontsize=12)
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3)
            
            # Time formatting
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Improving the layout
            plt.tight_layout()
            
            # Save the chart
            filename = f"{network}_gas_trend.png"
            filepath = os.path.join(self.chart_dir, filename)
            
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            # Очищаем старые файлы
            await self.cleanup_old_charts()
            
            logger.info(f"Chart saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating graph for {network}: {e}")
            return None
    
    async def generate_comparison_chart(self, all_history: Dict[str, List[GasData]]) -> Optional[str]:
        """
        Generate a comparative graph for all networks.
        """
        try:
            # Collecting data for comparison
            networks_data = {}
            
            for network, history in all_history.items():
                if not history:
                    continue
                
                # We take the last safe fees (p25)
                safe_fees = []
                for data in history[-100:]:  # Last 100 points
                    safe = data.get_fee_for_percentile("p25")
                    if safe is not None:
                        safe_fees.append(safe)
                
                if safe_fees:
                    networks_data[network] = safe_fees
            
            if not networks_data:
                logger.warning("No data available for comparison chart")
                return None
            
            # Создаем график
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Добавляем линии для каждой сети
            for network, fees in networks_data.items():
                style = self.styles.get(network, {"color": "gray", "name": network})
                
                # Создаем временную шкалу
                x = range(len(fees))
                
                ax.plot(x, fees,
                       label=style["name"],
                       color=style["color"],
                       linewidth=2,
                       alpha=0.8)
            
            ax.set_title("Gas Prices Comparison (Safe/25% percentile)", 
                        fontsize=16, fontweight='bold', pad=20)
            ax.set_ylabel("Gwei", fontsize=12)
            ax.set_xlabel("Last 100 samples", fontsize=12)
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            
            # Используем логарифмическую шкалу если нужно
            max_value = max(max(fees) for fees in networks_data.values())
            if max_value > 100:  # Если есть значения > 100 Gwei
                ax.set_yscale('log')
                ax.set_ylabel("Gwei (log scale)", fontsize=12)
            
            plt.tight_layout()
            
            # Сохраняем график
            filename = "all_networks_comparison.png"
            filepath = os.path.join(self.chart_dir, filename)
            
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"Comparison chart saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating comparison graph: {e}")
            return None
    
    async def generate_statistics_report(self, all_history: Dict[str, List[GasData]]) -> Optional[str]:
        """
        Generating a report with statistics.
        """
        try:
            report_lines = []
            report_lines.append("=" * 60)
            report_lines.append("GAS MONITOR STATISTICS REPORT")
            report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("=" * 60)
            
            for network, history in all_history.items():
                if not history:
                    continue
                
                network_config = config.networks.get(network)
                network_name = network_config.name if network_config else network
                
                report_lines.append(f"\n🔹 {network_name}")
                report_lines.append("-" * 40)
                
                # Собираем данные
                base_fees = []
                safe_fees = []
                fast_fees = []
                
                for data in history:
                    base_fees.append(data.base_fee)
                    
                    safe = data.get_fee_for_percentile("p25")
                    fast = data.get_fee_for_percentile("p75")
                    
                    if safe is not None:
                        safe_fees.append(safe)
                    if fast is not None:
                        fast_fees.append(fast)
                
                if base_fees:
                    current_base = base_fees[-1]
                    avg_base = np.mean(base_fees)
                    min_base = np.min(base_fees)
                    max_base = np.max(base_fees)
                    
                    report_lines.append(f"Base Fee: {current_base:.2f} Gwei")
                    report_lines.append(f"  Avg: {avg_base:.2f} | Min: {min_base:.2f} | Max: {max_base:.2f}")
                
                if safe_fees:
                    current_safe = safe_fees[-1]
                    avg_safe = np.mean(safe_fees)
                    
                    report_lines.append(f"Safe (25%): {current_safe:.2f} Gwei")
                    report_lines.append(f"  Average: {avg_safe:.2f} Gwei")
                
                if fast_fees:
                    current_fast = fast_fees[-1]
                    avg_fast = np.mean(fast_fees)
                    
                    report_lines.append(f"Fast (75%): {current_fast:.2f} Gwei")
                    report_lines.append(f"  Average: {avg_fast:.2f} Gwei")
                
                # Рассчитываем разницу safe-fast
                if safe_fees and fast_fees:
                    current_diff = current_fast - current_safe
                    avg_diff = avg_fast - avg_safe
                    
                    report_lines.append(f"Fast-Safe diff: {current_diff:.2f} Gwei")
                    report_lines.append(f"  Avg diff: {avg_diff:.2f} Gwei")
            
            report_lines.append("\n" + "=" * 60)
            report_lines.append("• RECOMMENDATIONS:")
            report_lines.append("• Low gas (< 20 Gwei): Good for transactions")
            report_lines.append("• Medium gas (20-35 Gwei): Wait if possible")
            report_lines.append("• High gas (> 35 Gwei): Avoid transactions")
            report_lines.append("=" * 60)
            
            # Сохраняем отчет
            report_text = "\n".join(report_lines)
            filename = f"gas_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            filepath = os.path.join(self.chart_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            logger.info(f"The report has been saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return None
    
    async def cleanup_old_charts(self):
        """Clearing old charts"""
        try:
            pattern = os.path.join(self.chart_dir, "*.png")
            files = sorted(glob.glob(pattern), key=os.path.getmtime)
            
            if len(files) > config.max_chart_files:
                files_to_delete = files[:-config.max_chart_files]
                
                for file in files_to_delete:
                    try:
                        os.remove(file)
                        logger.debug(f"The old schedule has been removed: {file}")
                    except Exception as e:
                        logger.error(f"Error deleting file {file}: {e}")
                
                logger.info(f"Deleted {len(files_to_delete)} old charts")
                
        except Exception as e:
            logger.error(f"Error clearing charts: {e}")
    
    async def cleanup(self):
        """Resource cleaning"""
        # Close all matplotlib figures
        plt.close('all')

# Global Graph Generator Instance
_chart_generator: Optional[ChartGenerator] = None

async def get_chart_generator() -> ChartGenerator:
    """Getting a global instance of the graph generator"""
    global _chart_generator
    
    if _chart_generator is None:
        _chart_generator = ChartGenerator()
    
    return _chart_generator

async def cleanup_charts():
    """Cleaning up the global graph generator instance"""
    global _chart_generator
    
    if _chart_generator:
        await _chart_generator.cleanup()
        _chart_generator = None