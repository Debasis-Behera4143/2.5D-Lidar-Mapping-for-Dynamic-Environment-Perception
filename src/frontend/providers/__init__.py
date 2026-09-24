"""
Frontend Data Provider Layer.

Provides unified abstraction for data ingestion:
- BaseDataProvider (Abstract Interface)
- SimulationDataProvider (Deterministic, high-fidelity engineering simulation)
- FastAPIDataProvider (Backend API client connector)
"""

from src.frontend.providers.base_provider import BaseDataProvider
from src.frontend.providers.simulation_provider import SimulationDataProvider
from src.frontend.providers.api_provider import FastAPIDataProvider

__all__ = ["BaseDataProvider", "SimulationDataProvider", "FastAPIDataProvider"]
