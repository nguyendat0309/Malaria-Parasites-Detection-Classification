"""
Core module for blood cell analysis.
Contains configuration, models, and pipeline logic.
"""

from core.config import cfg
from core.pipeline import AnalysisPipeline

__all__ = ['cfg', 'AnalysisPipeline']
