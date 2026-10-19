// TEST MINIMALE: solo seriale
#include <Arduino.h>

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("[SERIAL-ONLY] Boot OK");
}

void loop() {
    Serial.println("[SERIAL-ONLY] Loop attivo");
    delay(1000);
}
