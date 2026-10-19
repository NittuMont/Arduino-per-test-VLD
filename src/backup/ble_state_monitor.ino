
bool deviceConnected = false;


// Spostato in src/backup/ble_state_monitor.ino per test seriale
#include <BLEUtils.h>
#include <BLE2902.h>

// === UUIDs BLE custom ===
#define SERVICE_UUID        "b7e2e8c0-0000-4b1a-8e1e-000000000001"
#define STATE_CHAR_UUID     "b7e2e8c0-0001-4b1a-8e1e-000000000002"
#define ACK_CHAR_UUID       "b7e2e8c0-0002-4b1a-8e1e-000000000003"

// === Pinout ===
const uint8_t INPUT_PINS[6] = {2, 3, 4, 5, 6, 7}; // Modifica secondo cablaggio

// === Pinout LED ufficiale Arduino Nano ESP32 ABX00083 ===
#define LED_RED      46   // RGB LED Rosso (active-LOW)
#define LED_GREEN     0   // RGB LED Verde (active-LOW)
#define LED_BLUE     45   // RGB LED Blu (active-LOW)
#define LED_BUILTIN  48   // LED giallo onboard

// === Stato ===

volatile uint8_t circuitState = 0; // bit 0-5: stato ingressi
volatile bool stateChanged = false;
volatile unsigned long lastChangeTime = 0;
volatile bool ackReceived = false;
volatile bool waitingAck = false;

// === BLE ===
BLECharacteristic *stateChar;

BLECharacteristic *ackChar;
BLEServer *bleServer;


// === Trasmissione ===
const uint32_t RETRANSMIT_INTERVAL_MS = 20;
const uint32_t TIMEOUT_MS = 150;
uint8_t lastSentState = 0;
unsigned long transmitStart = 0;
unsigned long lastTransmit = 0;

// === LED ===
void rgbSet(bool r, bool g, bool b) {
    // Active-LOW: LOW = acceso, HIGH = spento
    digitalWrite(LED_RED,   r ? LOW : HIGH);
    digitalWrite(LED_GREEN, g ? LOW : HIGH);
    digitalWrite(LED_BLUE,  b ? LOW : HIGH);
}
void rgbOff() {
    digitalWrite(LED_RED,   HIGH);
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_BLUE,  HIGH);
}
void ledPairing() {
    static bool toggle = false;
    toggle = !toggle;
    if (toggle) rgbSet(false, false, true); // blu
    else        rgbOff();
}
void ledConnected() {
    rgbSet(false, true, false); // verde
}
void ledError() {
    rgbSet(true, false, false); // rosso
}

// === ISR ===
void IRAM_ATTR handleInputChange() {
    unsigned long now = millis();
    if (now - lastChangeTime < 10) return; // debounce 10ms
    lastChangeTime = now;
    uint8_t state = 0;
    for (uint8_t i = 0; i < 6; ++i) {
        if (digitalRead(INPUT_PINS[i]) == LOW) state |= (1 << i);
    }
    circuitState = state;
    stateChanged = true;
}

// === BLE Callbacks ===
class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer*) override {
        deviceConnected = true;
        Serial.println("[BLE] Client connesso");
    }
    void onDisconnect(BLEServer*) override {
        deviceConnected = false;
        Serial.println("[BLE] Client disconnesso");
    }
};
class AckCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pChar) override {
        ackReceived = true;
        Serial.println("[BLE] ACK ricevuto");
    }
};

// === Setup ===
void setup() {
    Serial.begin(115200);
    delay(300);
    Serial.println("[BOOT] Avvio firmware BLE State Monitor");
    Serial.println("[BOOT] Pin LED: Rosso=46, Verde=0, Blu=45, Builtin=48 (active-LOW)");
    pinMode(LED_RED,     OUTPUT);
    pinMode(LED_GREEN,   OUTPUT);
    pinMode(LED_BLUE,    OUTPUT);
    pinMode(LED_BUILTIN, OUTPUT);
    rgbOff();
    digitalWrite(LED_BUILTIN, LOW);
    Serial.println("[BOOT] LED RGB onboard inizializzati");
    for (uint8_t i = 0; i < 6; ++i) {
        pinMode(INPUT_PINS[i], INPUT_PULLUP);
        attachInterrupt(digitalPinToInterrupt(INPUT_PINS[i]), handleInputChange, CHANGE);
    }
    Serial.println("[BOOT] Ingressi digitali configurati");
    BLEDevice::init("NanoESP32-RelayMonitor");
    Serial.println("[BLE] BLEDevice inizializzato");
    bleServer = BLEDevice::createServer();
    bleServer->setCallbacks(new ServerCallbacks());
    BLEService *service = bleServer->createService(SERVICE_UUID);
    stateChar = service->createCharacteristic(
        STATE_CHAR_UUID,
        BLECharacteristic::PROPERTY_NOTIFY
    );
    stateChar->addDescriptor(new BLE2902());
    ackChar = service->createCharacteristic(
        ACK_CHAR_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    ackChar->setCallbacks(new AckCallbacks());
    service->start();
    Serial.println("[BLE] Servizio BLE avviato");
    bleServer->getAdvertising()->start();
    Serial.println("[BLE] Advertising avviato");
}

// === Loop ===
void loop() {
    static unsigned long lastLed = 0;
    unsigned long now = millis();
    static bool lastConnected = false;
    // LED stato
    if (!deviceConnected) {
        // Advertising: lampeggio blu
        if (now - lastLed > 250) {
            ledPairing();
            lastLed = now;
        }
        if (lastConnected) {
            Serial.println("[BLE] Dispositivo disconnesso, advertising attivo");
            lastConnected = false;
        }
        waitingAck = false;
        ackReceived = false;
    } else if (waitingAck) {
        // errore timeout
        if (now - transmitStart > TIMEOUT_MS) {
            ledError();
            Serial.println("[BLE] Timeout ACK, reset stato");
            waitingAck = false;
            ackReceived = false;
        } else {
            // Connessione BLE attiva, verde fisso
            if (!lastConnected) {
                ledConnected();
                Serial.println("[BLE] Client connesso, LED verde fisso");
                lastConnected = true;
            }
        }
    } else {
        // Connessione BLE attiva, verde fisso
        if (!lastConnected) {
            ledConnected();
            Serial.println("[BLE] Client connesso, LED verde fisso");
            lastConnected = true;
        }
    }

    // Watchdog software: se il LED non è blu in advertising, forza lampeggio
    if (!deviceConnected && !digitalRead(LED_BLUE)) {
        // Se il blu non lampeggia, forzalo
        ledPairing();
    }
    // Trasmissione stato
    if (deviceConnected && (stateChanged || waitingAck)) {
        if (!waitingAck) {
            lastSentState = circuitState;
            transmitStart = now;
            waitingAck = true;
            ackReceived = false;
            stateChanged = false;
        }
        if (ackReceived) {
            waitingAck = false;
            ackReceived = false;
            Serial.println("[BLE] ACK ricevuto, trasmissione completata");
        } else if (now - lastTransmit >= RETRANSMIT_INTERVAL_MS) {
            stateChar->setValue(&lastSentState, 1);
            stateChar->notify();
            lastTransmit = now;
            Serial.printf("[BLE] NOTIFY stato: 0x%02X\n", lastSentState);
        }
    }
    // Watchdog: se resta troppo in uno stato non valido, resetta
    static unsigned long lastLoop = 0;
    if (now - lastLoop > 5000) {
        Serial.println("[WATCHDOG] Reset per sicurezza");
        ESP.restart();
    }
    lastLoop = now;
    delay(0); // cede il controllo al task BLE
}
