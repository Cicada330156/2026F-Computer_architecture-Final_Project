import threading
import queue
import time
from pocketsphinx import LiveSpeech
import serial
from serial.tools import list_ports

# Thread-safe queue to pass recognized speech across threads
speech_queue = queue.Queue()
arduino_tx_queue = queue.Queue()
arduino_rx_queue = queue.Queue()

ARDUINO_BAUD_RATE = 9600

def detect_arduino_port():
    """Find an Arduino serial port, or the only available serial port."""
    ports = list(list_ports.comports())
    arduino_ports = [
        port for port in ports
        if "arduino" in " ".join(filter(None, (port.description, port.manufacturer, port.product))).lower()
    ]
    if len(arduino_ports) == 1:
        return arduino_ports[0].device
    if len(arduino_ports) > 1:
        raise serial.SerialException("Multiple Arduino serial ports found")
    if len(ports) == 1:
        return ports[0].device
    raise serial.SerialException("Arduino serial port not found; connect one or configure port selection")

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


def arduino_worker():
    """Forward queued commands to the Arduino and queue its responses."""
    print("[Arduino Worker] Connecting to Arduino...")
    try:
        arduino_port = detect_arduino_port()
        print(f"[Arduino Worker] Using serial port {arduino_port}.")
        with serial.Serial(arduino_port, ARDUINO_BAUD_RATE, timeout=0.1) as arduino:
            # Many Arduino boards reset when the serial port is opened.
            time.sleep(2)
            print("[Arduino Worker] Connected.")
            while True:
                try:
                    message = arduino_tx_queue.get_nowait()
                    arduino.write((message + "\n").encode("utf-8"))
                    arduino_tx_queue.task_done()
                except queue.Empty:
                    pass

                response = arduino.readline().decode("utf-8", errors="replace").strip()
                if response:
                    arduino_rx_queue.put(response)
    except serial.SerialException as exc:
        print(f"[Arduino Worker] Serial connection failed: {exc}")

# 1. Start PocketSphinx listener in background thread
# Daemon=True ensures thread exits automatically when main program stops
listener_thread = threading.Thread(target=pocketsphinx_worker, daemon=True)
listener_thread.start()
arduino_thread = threading.Thread(target=arduino_worker, daemon=True)
arduino_thread.start()

# Example phrase-to-command mapping; adapt commands to the Arduino sketch.
phrase_commands = {
    "fire": "fire",
    "shoot": "fire",
    "safety on": "safety on",
    "turn on safety": "safety on",
    "turn on the safety": "safety on",
    "safety off": "safety off",
    "turn off safety": "safety off",
    "turn off the safety": "safety off"
}

# 2. Main NonBlocking App Loop
print("[Main] Application started. Doing other work...")
try:
    while True:
        # Check queue for new text w/o blocking (block=False)
        try:
            recognized_text = speech_queue.get_nowait()
            print(f"\n[Main] Received Speech: '{recognized_text}'")

            command = phrase_commands.get(recognized_text.lower().strip())
            if command:
                arduino_tx_queue.put(command)
                print(f"[Main] Queued Arduino command: {command}")
            
            speech_queue.task_done()
        except queue.Empty:
            # No new speech detected in this tick
            pass

        # Display any messages received from the Arduino.
        try:
            arduino_message = arduino_rx_queue.get_nowait()
            print(f"\n[Main] Arduino: '{arduino_message}'")
            arduino_rx_queue.task_done()
        except queue.Empty:
            pass

        # Simulate your main program's responsibilities or UI loop
        print(".", end="", flush=True)
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting app safely")
