#include "analog_PressureSensor.h"
#include "i2c_PressureSensor.h"
#include "handleSerialCommands.h"
#include "allSettings.h"
#include "valvePair.h"
#include "bangBang.h"
#include "proportional.h"
#include "pidFull.h"

//SENSING:
  //Arduino ADC pins:
    //Mega:  A0-A15                        (all pins work fine)
    //Uno:   A0-A5                         (all pins work fine)
    //Micro: A0, A1, A4 - A8, A11          (A9, A10, A12, A13 all conflict with PWM pins)
    //Nano:  A0-A7                         (A4, A5 are i2c pins)

//VALVES:
  //Arduino PWM pins:
    //Mega:  2 - 13, 44, 45, 46            (all pins work fine)
    //Uno:   3, 5, 6, 9, 10, 11            (all pins work fine)
    //Micro: 3, 5, 6, 9, 10, 11, 12, 13    (all pins work fine)
    //Nano:  3, 6, 9, 10, 11               (pin 5 fails consistently, no idea why)




//Define the type of sensor to use (only one can be true)
#define SENSOR_ANALOG true
#define SENSOR_I2C false

#define SENSOR_MODEL 1
#define NUM_SENSORS 3

//Define the type of controller to use (only one can be true)
#define CONTROL_BANGBANG false
#define CONTROL_P false
#define CONTROL_PID true


//Set default settings for things
//If using i2c sensors...
  int sensorAddr=0x58;
  bool useMux=true;
  int muxAddr=0x70;

//Set valve pins
  int valvePins[][2]= { {6,9}, {10,11} };

//Default controller settings
  float deadzone_start=0.0;
  float setpoint_start=0;
  float pid_start[]={1.0,0.1,0.1}; 
  float integratorResetTime_start = 50;


//Create a new settings object
globalSettings settings;
controlSettings ctrlSettings[NUM_SENSORS];
sensorSettings senseSettings[NUM_SENSORS];

//Create an object to handle serial commands
handleSerialCommands handleCommands;

//Set up sensing
#if(SENSOR_ANALOG)
  int senseChannels[]={A0,A1,A2,A3};
  analog_PressureSensor sensors[NUM_SENSORS];
#elif(SENSOR_I2C)
  int senseChannels[]={0,1,2,3};
  i2c_PressureSensor sensors[NUM_SENSORS];
#endif

int ave_len=10;
float pressures[NUM_SENSORS];
float valveSets[NUM_SENSORS];


//Set up valve pairs  
valvePair valves[NUM_SENSORS];


//Create an array of controller objects for pressure control
#if CONTROL_BANGBANG
  bangBang controllers[NUM_SENSORS];
#elif CONTROL_P
  proportional controllers[NUM_SENSORS];
#elif CONTROL_PID
  pidFull controllers[NUM_SENSORS];
#endif 



//Set up output task manager variables
unsigned long previousTime=0;
unsigned long currentTime=0;




//______________________________________________________________________
void setup() {
  //Start serial
    Serial.begin(115200);
    //Serial.flush();
    Serial.setTimeout(10);
 
  //Initialize control settings
    handleCommands.initialize(NUM_SENSORS);
    handleCommands.startBroadcast();
    for (int i=0; i<NUM_SENSORS; i++){
      
      //Initialize control settings
      ctrlSettings[i].setpoint=setpoint_start;
      
      if(CONTROL_BANGBANG){
        ctrlSettings[i].deadzone=deadzone_start;
      }
      else if (CONTROL_P || CONTROL_PID){
        for (int j=0; j<3; j++){
          ctrlSettings[i].pidGains[j]=pid_start[j];
          ctrlSettings[i].deadzone=deadzone_start;
          ctrlSettings[i].integratorResetTime=integratorResetTime_start;
        }
      }


      //Initialize sensor settings
      senseSettings[i].sensorModel=SENSOR_MODEL;

      if(SENSOR_ANALOG){
        senseSettings[i].sensorPin=senseChannels[i];
      }
      else if(SENSOR_I2C){
        senseSettings[i].sensorAddr= sensorAddr;
        senseSettings[i].useMux     = useMux;
        senseSettings[i].muxAddr    = muxAddr;
        senseSettings[i].muxChannel = senseChannels[i];
      }
      
    }


  //Initialize the pressure sensor and control objects
    for (int i=0; i<NUM_SENSORS; i++){
      sensors[i].initialize(senseSettings[i]);
      valves[i].initialize(valvePins[i][0],valvePins[i][1]);
      controllers[i].initialize(ctrlSettings[i]);
    }


    
    settings.looptime =0;
    settings.outputsOn=false;
}




//______________________________________________________________________
void loop() {
  //Serial.println("_words need to be here (for some reason)");
  //Handle serial commands
   bool newSettings=handleCommands.go(settings, ctrlSettings);
  
  //Get pressure readings
    for (int i=0; i<NUM_SENSORS; i++){
      //Serial.println("Inside the for loop");
      //Get the new pressures
      sensors[i].getData();
      pressures[i] = sensors[i].getPressure();
      
      //Update controller settings
      if (newSettings){
        controllers[i].updateSettings(ctrlSettings[i]);
        controllers[i].setSetpoint(ctrlSettings[i].setpoint);
      }

      //Run 1 step of the controller
      valveSets[i] = controllers[i].go(pressures[i]);

      //Send new actuation signal to the valves
      valves[i].go( valveSets[i] );
      
      //Serial.print('\n');
    }

  //Print out data at close to the correct rate
  currentTime=millis();
  if (settings.outputsOn && (currentTime-previousTime>= settings.looptime)){
    printData();
    previousTime=currentTime;
  }
    
  
}


//______________________________________________________________________


//PRINT DATA OUT FUNCTION
void printData(){
  //Serial.print(currentTime);
  //Serial.print('\t');
  //Serial.print(currentTime-previousTime);
  //Serial.print('\t');
  for (int i=0;i<NUM_SENSORS;i++){
    Serial.print(pressures[i],5);
    Serial.print('\t');  
  }
  Serial.print('\n');
  
}


