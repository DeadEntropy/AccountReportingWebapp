"""Code to profile the app"""

from datetime import datetime

import cProfile

# Importing app runs initialize_managers, which is what the profiled callbacks read from.
# register_callbacks returns its callbacks keyed by name: they are closures over the managers and
# are not importable from app's module scope.
import app


def run_server():
    """Code to profile goes here"""

    app.callbacks["update_tab_2"](2024, "SubType: Grocery")


def run_app_with_profiling():
    # Create a profiler object
    profiler = cProfile.Profile()
    time_stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # Start profiling
    profiler.enable()

    # Run the server in a separate thread
    run_server()

    # After Enter, stop profiling and exit
    profiler.disable()

    profiler.dump_stats(f"profile_{time_stamp}.prof")

    print("Done profiling.")


if __name__ == "__main__":
    run_app_with_profiling()
