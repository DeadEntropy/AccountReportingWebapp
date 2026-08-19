"""Code to profile the app"""

from datetime import datetime

import cProfile, pstats


from app import update_tab_2  # Import the function to profile


def run_server():
    """Code to profile goes here"""

    update_tab_2(2024, "SubType: Grocery")


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
