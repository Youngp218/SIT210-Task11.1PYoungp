//myChannelNumber, myWriteAPIKey, WIFI_SSID, WIFI_PASS
#include "arduino_secrets.h"
#include <BH1750.h>
#include <Wire.h>
#include <WiFiNINA.h>
#include "arduino_secrets.h"
#include "ThingSpeak.h" 

#define CYCLES 50
BH1750 lightMeter;

// Sensor pins
const int tempPin = A0;
const int soundAPin = A1; //for actual values
const int soundDPin = 13; //for digital interrupts
const int soilPin = A2;
const int soilPowerPin = 7; // for control over power output to the soil moisture sensor

const unsigned long myChannelNumber = CHANNEL_ID;
const char myWriteAPIKey[] = WRITE_KEY;
const char ssid[] = SECRET_SSID; // network SSID 
const char pass[] = SECRET_PASS; // network password
WiFiClient  client;

float tmp = 0;
int sound = 0;
int soil = 0;
int i = 0;
void setup() {
  Serial.begin(115200);
  while (!Serial);

  pinMode(soilPowerPin, OUTPUT); // need to disconnect the soil sensor when unused to prevent corrosion

  Serial.print("Connecting to Thingspeak");
  ThingSpeak.begin(client);
  
  Wire.begin();

  lightMeter.begin();
  
  attachInterrupt(digitalPinToInterrupt(soundDPin), updateSound, RISING);
}

void loop() {
  connectWifi();
  digitalWrite(soilPowerPin, HIGH);
  delay(20);
  if (i < CYCLES) { //collect analog values to average
    tmp += checkTemp();
    //sound - add digital pin interrupt which records analog value when activated, then in this section, check the recorded/current sound, and record the louder
    // soil - follow temp
    soil += analogRead(soilPin);
    //record the loudest reading
    int snd = analogRead(soundAPin);
    if (snd > sound) sound = snd;
    i += 1;
  } else { // send data to thingspeak 
    float avgTmp = tmp/(float)CYCLES;
    float avgSoil = soil/(float)CYCLES;
    // reset counter/value for next time
    i = 0;
    tmp = 0.0;
    float lux = lightMeter.readLightLevel();
    
    updateThingspeak(avgTmp, sound * 0.1, avgSoil, lux);
    sound = 0;
    delay(5000); // Wait 5 seconds to update the channel again
  }
}

float checkLux() {
  float lux = lightMeter.readLightLevel();
  Serial.print("Light: ");
  Serial.print(lux);
  Serial.println(" lx");
  return lux;
}

float checkTemp() {
  int reading = analogRead(tempPin);  
  // temperature reading is proportional to voltage applied
  float voltage = reading * 3.3;
  // in celsius
  float temp = (voltage/1024 - 0.5)*100;
  return temp; 
}

void updateSound() {
  int snd = analogRead(soundAPin);
  if (snd > sound) sound = snd;
}

void connectWifi() {
  // Connect or reconnect to WiFi
  if(WiFi.status() != WL_CONNECTED){
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(SECRET_SSID);
    while(WiFi.status() != WL_CONNECTED){
      WiFi.begin(ssid, pass);
      Serial.print(".");
      delay(5000);     
    } 
    Serial.println("\nConnected.");
  }
}

void updateThingspeak(float tmpReading, float soundReading, float soilReading, float luxReading) {
  // set the fields with the values
  ThingSpeak.setField(1, luxReading);
  ThingSpeak.setField(2, soilReading);
  ThingSpeak.setField(3, tmpReading);
  ThingSpeak.setField(4, soundReading);
  
  // write to the ThingSpeak channel 
  int x = ThingSpeak.writeFields(myChannelNumber, myWriteAPIKey);
  if(x == 200){
    Serial.println("Channel update successful.");
  } else {
    Serial.println("Problem updating channel. HTTP error code " + String(x));
  }
}
