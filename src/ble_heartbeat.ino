// --- Pacchetti protocollo ---
// Protocollo semplificato: solo stato circuiti
#define PKT_TYPE_STATE 0x00
// BLE firmware con heartbeat LED blu (active-low)
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

bool justConnected = false;
bool deviceConnected = false;
// --- DEFINIZIONI MACRO E VARIABILI GLOBALI ORDINATE ---
#define LED_RED 14    // active-low
#define LED_GREEN 15  // active-low
#define LED_BLUE 16   // active-low (heartbeat)
#define LED_YELLOW 13 // active-high (opzionale)

#define SERVICE_UUID        "b7e2e8c0-0000-4b1a-8e1e-000000000001"
#define STATE_CHAR_UUID     "b7e2e8c0-0001-4b1a-8e1e-000000000002"
#define ACK_CHAR_UUID       "b7e2e8c0-0002-4b1a-8e1e-000000000003"


// Nuova mappatura pin-circuiti e nomi (2026-04):
// D2:  AD OFF
// D3:  AD ON
// D6:  AL OFF
// D7:  AL ON
// D11: AT OFF
// D12: AT ON

#define PIN_AD_OFF 2   // D2
#define PIN_AD_ON  3   // D3
#define PIN_AL_OFF 6   // D6
#define PIN_AL_ON  7   // D7
#define PIN_AT_OFF 11  // D11
#define PIN_AT_ON  12  // D12

// Ordine per stato BLE e GUI:
// [AT ON, AL ON, AD ON, AT OFF, AL OFF, AD OFF]
const uint8_t CIRCUIT_PINS[6] = {
    PIN_AT_ON,   // 0
    PIN_AL_ON,   // 1
    PIN_AD_ON,   // 2
    PIN_AT_OFF,  // 3
    PIN_AL_OFF,  // 4
    PIN_AD_OFF   // 5
};

BLEServer *bleServer = nullptr;
BLECharacteristic *stateChar = nullptr;
uint8_t lastState = 0;
uint8_t seqNum = 0;

// --- FINE DEFINIZIONI MACRO E VARIABILI GLOBALI ---

// --- CALLBACK BLE ---




class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer*) override {
        deviceConnected = true;
        Serial.println("[BLE] Client connesso");
        // Attendi comando READY dalla GUI anche dopo una riconnessione
        justConnected = true;
    }
    void onDisconnect(BLEServer*) override {
        deviceConnected = false;
        Serial.println("[BLE] Client disconnesso");
        // Riavvia advertising per rendere il device nuovamente visibile
        if (bleServer) {
            bleServer->getAdvertising()->start();
            Serial.println("[BLE] Advertising riavviato dopo disconnessione");
        }
    }
};



void setup() {
    Serial.begin(115200);
    delay(300);
    Serial.println("[BOOT] Avvio firmware BLE con heartbeat LED blu");
    pinMode(LED_RED, OUTPUT);
    pinMode(LED_GREEN, OUTPUT);
    pinMode(LED_BLUE, OUTPUT);
    pinMode(LED_YELLOW, OUTPUT);
    digitalWrite(LED_RED, HIGH);
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_BLUE, HIGH);
    digitalWrite(LED_YELLOW, LOW); // spento (active-high)

    // Imposta i pin dei circuiti come input con pullup
    for (int i = 0; i < 6; ++i) {
        pinMode(CIRCUIT_PINS[i], INPUT_PULLUP);
    }

    BLEDevice::init("NanoESP32-RelayMonitor");
    bleServer = BLEDevice::createServer();
    bleServer->setCallbacks(new ServerCallbacks());
    BLEService *service = bleServer->createService(SERVICE_UUID);
    stateChar = service->createCharacteristic(
        STATE_CHAR_UUID,
        BLECharacteristic::PROPERTY_NOTIFY
    );
    stateChar->addDescriptor(new BLE2902());
    // Caratteristica di scrittura per comando READY
    class ReadyCallback : public BLECharacteristicCallbacks {
        void onWrite(BLECharacteristic* pCharacteristic) override {
            std::string value = pCharacteristic->getValue();
            if (value == "READY") {
                uint8_t state = 0;
                for (int i = 0; i < 6; ++i) {
                    if (digitalRead(CIRCUIT_PINS[i]) == LOW) state |= (1 << i);
                }
                if (stateChar) {
                    stateChar->setValue(&state, 1);
                    stateChar->notify();
                    Serial.print("[BLE] Stato inviato su comando READY: ");
                    Serial.println(state, BIN);
                }
            }
        }
    };
    BLECharacteristic *readyChar = service->createCharacteristic(
        ACK_CHAR_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    readyChar->setCallbacks(new ReadyCallback());
    service->start();
    bleServer->getAdvertising()->start();
    Serial.println("[BLE] Advertising avviato");
    // Calcola stato iniziale ma NON inviare notifica qui
    lastState = 0;
    for (int i = 0; i < 6; ++i) {
        if (digitalRead(CIRCUIT_PINS[i]) == LOW) lastState |= (1 << i);
    }
}

void loop() {
    static uint8_t lastState = 0;
    static unsigned long lastBeat = 0;
    static bool ledOn = false;
    unsigned long now = millis();

    if (!deviceConnected) {
        // Heartbeat: lampeggio lento LED blu (active-low)
        if (now - lastBeat > 500) {
            ledOn = !ledOn;
            digitalWrite(LED_BLUE, ledOn ? LOW : HIGH); // active-low
            lastBeat = now;
        }
        return;
    }

    uint8_t state = 0;
    for (int i = 0; i < 6; ++i) {
        if (digitalRead(CIRCUIT_PINS[i]) == LOW) state |= (1 << i);
    }
    if (state != lastState) {
        uint8_t packet[3] = {PKT_TYPE_STATE, seqNum, state};
        stateChar->setValue(packet, 3);
        stateChar->notify();
        Serial.print("[CIRCUITI] Inviato stato seq ");
        Serial.print(seqNum);
        Serial.print(": ");
        Serial.println(state, BIN);
        lastState = state;
        seqNum = (seqNum + 1) & 0xFF;
    }
    // LED blu fisso
    digitalWrite(LED_BLUE, LOW); // acceso (active-low)
    delay(10); // cede il controllo
}
