#!/usr/bin/env python3
import logging
import sys
from experiments.collective_learning import CollectiveLearningBase


logger = logging.getLogger("ml_service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


if __name__ == "__main__":
    e = CollectiveLearningBase()
    e.start(["collective_learning_exp003"], "global")
    input("Press key to stop.")
    e.stop()
