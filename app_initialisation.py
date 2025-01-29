# app_initialisation.py
import configparser
import os

from bkanalysis.config import config_helper as ch
from bkanalysis.managers import DataManager, MarketManager, TransformationManagerCache, FigureManager


def initialize_managers(ref_currency: str, default_year: int):
    """initialise the managers"""
    config = configparser.ConfigParser()
    if len(config.read(ch.source)) != 1:
        raise OSError(f"no config found in {ch.source}")

    data_path = os.getenv('DATA_PATH', '/data')

    data_manager = DataManager(config)
    data_manager.load_pregenerated_data(os.path.join(data_path, "data_manager.csv"))

    market_manager = MarketManager(ref_currency)
    market_manager.load_pregenerated_data(os.path.join(data_path, "data_market.csv"))

    transformation_manager = TransformationManagerCache(data_manager, market_manager, default_year, None, ["both", "out"])

    figure_manager = FigureManager(transformation_manager)

    return data_manager, market_manager, transformation_manager, figure_manager
