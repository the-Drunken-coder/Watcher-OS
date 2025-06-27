import logging
from .engine import WatcherEngine

def main():
    """
    Main function to start the Watcher OS application.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Watcher OS...")
        engine = WatcherEngine()
        engine.run()
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}", exc_info=True)
    finally:
        logger.info("Watcher OS has shut down.")

if __name__ == '__main__':
    main() 