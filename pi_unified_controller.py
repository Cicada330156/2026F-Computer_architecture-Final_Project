import threading
import queue
import time
from pocketsphinx import LiveSpeech

# Thread-safe queue to pass recognized speech across threads
speech_queue = queue.Queue()

def pocketsphinx_worker():
    """
    Background worker continuously listens to mic.
    Blocks internally but runs on separate thread, keeps main loop free.
    """
    print("[Sphinx Worker] Starting microphone listener...")
    # Initialize LiveSpeech (blocks internally)
    speech = LiveSpeech(
        verbose=False,
        sampling_rate=16000,
        buffer_size=2048,
        no_search=False,
        full_utt=False
    )
    
    for phrase in speech:
        text = str(phrase).strip()
        if text:
            # Put recognized text into queue, no block
            speech_queue.put(text)

# 1. Start PocketSphinx listener in background thread
# Daemon=True ensures thread exits automatically when main program stops
listener_thread = threading.Thread(target=pocketsphinx_worker, daemon=True)
listener_thread.start()

# 2. Main NonBlocking App Loop
print("[Main] Application started. Doing other work...")
try:
    while True:
        # Check queue for new text w/o blocking (block=False)
        try:
            recognized_text = speech_queue.get_nowait()
            print(f"\n[Main] Received Speech: '{recognized_text}'")
            
            # ---> HANDOFF TO ANOTHER PROGRAM HERE <---
            # Example: Send to another local script or process via subprocess, sockets, or HTTP.
            
            speech_queue.task_done()
        except queue.Empty:
            # No new speech detected in this tick
            pass

        # Simulate your main program's responsibilities or UI loop
        print(".", end="", flush=True)
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting app safely")
