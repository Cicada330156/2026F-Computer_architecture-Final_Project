#include <Arduino.h>

const uint8_t SAFETY = 2;
const uint8_t SPINNER = 3;
const uint8_t PUSHER = 4;

String instruction = "";

bool safe = true;

// Tracks the inverse of the SAFETY pin output.
void setSafety(bool value) {
    digitalWrite(SAFETY, value ? LOW : HIGH);
    safe = value;
}

String fire(int n) {
	if (safe) {
			return "\"error\":\"safety_on\"";
	}

    
	digitalWrite(SPINNER, HIGH);
	delay(500);
	digitalWrite(PUSHER, HIGH);
	delay(150*n-50);
	digitalWrite(PUSHER, LOW);
	delay(500);
	digitalWrite(SPINNER, LOW);
	return "\"result\":\"fire_success\"";
}

String fire() {
	fire(1);
}

void setup() {
	Serial.begin(9600);
	setSafety(false);
	digitalWrite(SPINNER, LOW);
	digitalWrite(PUSHER, LOW);

	pinMode(SAFETY, OUTPUT);
	pinMode(SPINNER, OUTPUT);
	pinMode(PUSHER, OUTPUT);

	Serial.println("I'm alive!");
}

int i = 1;
void loop() {
	if (Serial.available() > 0) {
		instruction = Serial.readString();
		instruction.trim();
		if (instruction == "fire") {
			Serial.println(fire());
		} else if (instruction == "safety on") {
			setSafety(true);
		} else if (instruction == "safety off") {
			setSafety(false);
		}else {
			Serial.println(instruction);
		}
	}
}

