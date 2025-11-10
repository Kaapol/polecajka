import subprocess
import sys
from pathlib import Path
from watchfiles import watch

if __name__ == "__main__":
    process = None


    def start_server():
        global process
        print("\n🚀 Starting server...\n")
        process = subprocess.Popen(
            [sys.executable, "-m", "flask", "--app", "app", "run", "--no-reload"],
            cwd=Path(__file__).parent
        )


    def should_reload(change_type, path):
        """Filtruj tylko pliki które nas interesują"""
        return str(path).endswith(('.py', '.html', '.css', '.js'))


    def watch_changes():
        global process
        start_server()

        for changes in watch(".", watch_filter=should_reload):
            print("\n📝 Detected changes, restarting...\n")
            if process:
                process.terminate()
                process.wait()
            start_server()


    try:
        watch_changes()
    except KeyboardInterrupt:
        print("\n✋ Shutting down...")
        if process:
            process.terminate()
            process.wait()
        sys.exit(0)