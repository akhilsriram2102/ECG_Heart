"""
pipeline.py — Orchestrates the full ETL pipeline.

Run directly:
    python -m etl.pipeline
"""

import logging
import sys
from pathlib import Path

from etl.extract import extract
from etl.transform import transform
from etl.load import load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path(__file__).resolve().parents[1] / "logs" / "pipeline.log",
            mode="a",
        ),
    ],
)

logger = logging.getLogger(__name__)


def run_pipeline(source_path=None) -> dict:
    """Execute Extract → Transform → Load and return output paths."""
    logger.info("========== Heart Disease ETL Pipeline START ==========")

    logger.info("STAGE 1/3 — Extract")
    raw_df = extract(source_path)

    logger.info("STAGE 2/3 — Transform")
    transformed = transform(raw_df)

    logger.info("STAGE 3/3 — Load")
    outputs = load(transformed)

    logger.info("========== Pipeline COMPLETE ==========")
    for key, path in outputs.items():
        logger.info("  %-15s → %s", key, path)

    return outputs


if __name__ == "__main__":
    run_pipeline()
