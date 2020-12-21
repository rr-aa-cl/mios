#!/usr/bin/env python3
import logging
import sys
from experiments.collective_learning import CollectiveLearningBase
#from experiments.collective_learning_test import CollectiveLearningBase


logger = logging.getLogger("ml_service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


if __name__ == "__main__":
    e = CollectiveLearningBase()
    e.start(["collective_learning_insertion_001"], "global", "similar", "collective-panda-002",
            "collective_learning_insertion_screen_001", 1.15)
    input("Press key to stop.")
    e.stop()
