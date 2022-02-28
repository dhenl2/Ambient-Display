# Ambient-Display Project - SHED
The project SHED, Shed Hex Environment Display, contains the codebase for components of an Ambient Display system utilised in the Sunnybank Men's Shed. The Ambient Display project was designed to indicate the current activity level within the Men's Shed environment using colours and animations shown on the display. The system utilises ESP8266 for filtered sensor ouput and ambient display control and a Raspberry Pi 3A+ for communication management, data analysis and activity level allocation via a dynamic normal distribution. The intention of this implementation was for this project to require minimal interaction with the members of the Men's Shed, reducing the need for inductions into the operations of the system. As a result, a selected supervisor was only required to turn on and off the display during periods of active hours.  
<img src="https://user-images.githubusercontent.com/69876000/155920770-782350b9-562d-4275-9f61-e0e437a07150.png" alt="drawing" width="600"/>

## Communication Hub and Command Centre
This component is controlled by the Raspberry Pi 3A+, utilising a locally hosted WIFI network to establish client-server communication. The server is intented to be run upon startup of the Pi, logging data collected for later analysis and failure points for debugging. As the Pi is unable to update system time due to a lack of an internet connection, a GPS sensor was added to attain GPS time for setting the correct system time. This was crucial, as data logs needed to be correlated real-time events for post analysis. The current activity levels of the environment are determined by assuming a normal distribution of the data received from both the audio and entrance monitoring devices. Calibration of this distribution is done periodically to update the mean and standard deviation utilised to determine the activity level of the sensor data. The audio and entrance monitors are each allocated their own distribution, with the final activity level to be displayed determined by the ceiling of the average of the two respective levels. Source files for this component can be found in **"server_src"** directory.

## Microphone Client
This component contains an ESP8266 and a microphone sensor. The received raw data was converted to dB readings that are later sent to the communication hub for processing. The device communicates to the server asnychronously via uasyncio. Source files for this component can be found in **"microphone_src"** directory.  
<img src="https://user-images.githubusercontent.com/69876000/155922201-88ad8b5a-660e-4bc2-a8b6-104440923000.jpg" alt="drawing" height="600"/>

## Entrance Monitor Client
This component contains an ESP8266 and two ultra-sound sensors placed a distance apart. The application of this component was to determine people entering and leaving the space to establish the room occupancy levels of common work spaces. The correct application of this concept required raw sensor filtering for removing false positives and irregularities in the input received. The device communicates to the server asnychronously via uasyncio. Source files for this component can be found in **"door_sensor_src"** directory.  
<img src="https://user-images.githubusercontent.com/69876000/155922523-eca13c01-ee2f-404c-bd09-656babc3f7ce.jpg" alt="drawing" width="600"/>

## Ambient Display Client
This component contains an ESP8266 and a borrowed display project from a colleague at UQ. This device is commanded via the command centre to display the determined activity level of the environment. As this display was borrowed to reduce the workload on myself in designing and constructing a display, the visualisation may be odd. The display indicates activity levels by a combined visualisation of colour and animation speed. The activity levels 1 to 6, or slight to excessive activity, are indicated by colours dark blue, light blue, green, yellow, orange and red. The animation itself is a horizontal animation moving from left to right. As the display is indicating the current activity level, with no transitions currently taking place, the entire display will indicate a singular colour.  
<img src="https://user-images.githubusercontent.com/69876000/155923342-5573b507-094f-41ac-ac45-6cb734e1111e.png" alt="drawing" width="200"/>
<img src="https://user-images.githubusercontent.com/69876000/155923346-731dd246-9b2d-4004-8eb2-9b9f75640ade.png" alt="drawing" width="200"/>
<img src="https://user-images.githubusercontent.com/69876000/155923349-9d44bb1e-d22e-4cd5-8f4f-16bdf7bfb6c4.png" alt="drawing" width="200"/>  

During periods where the display is changing activity levels, this is indicated via colours consuming the current level. For new levels higher than the current, these are introduced from the bottom and propogated upwards till they consume all 3 levels. For new levels lower than the current, these are introduced from the top and propogated downards till they consume all 3 levels.  
<img src="https://user-images.githubusercontent.com/69876000/155923806-577a2cd2-dc0c-470d-84e5-e15d2885ce9d.png" alt="drawing" width="200"/>
<img src="https://user-images.githubusercontent.com/69876000/155923810-be2bdd60-e274-4c29-87f3-56be173c84bc.png" alt="drawing" width="200"/>
<img src="https://user-images.githubusercontent.com/69876000/155923813-03fe2979-80cb-41d7-8961-400c82d7b8d2.png" alt="drawing" width="200"/>  
The device communicates to the server asnychronously via uasyncio. Source files for this component can be found in **"display_src"** directory.    
<img src="https://user-images.githubusercontent.com/69876000/155924735-6574aea8-99dd-44ae-8a79-2078a1015363.jpg" alt="drawing" width="600"/>



