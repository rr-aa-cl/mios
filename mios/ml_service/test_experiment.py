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
    e = CollectiveLearningBase("umuc2qio38kvg66et89pegfi6gmgb3", "ad1kq223m7rrropsmp9mefiewce193")
    e.start(["collective_learning_insertion_screen_01"], "global", "similar", "collective-panda-002")
    input("Press key to stop.")
    e.stop()
