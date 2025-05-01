# ESPMeter

## NOTE: THIS IS AN EARLY STAGE PROJECT AND THINGS ARE NOT PERFECT. USE AT OWN PERIL. I AM A HOBBY PROGRAMMER AND CAN ONLY PROVIDE EXTREMELY LIMITED SUPPORT IN CASE OF PROBLEMS

### Reading simple digital utility meters with Home Assistant, ESPHome and EasyOCR.

ESPMeter is a simple script, for now just setup to run in a docker container with Python, but could probably easily be made into a small Home Assistant Addon by someone more capable than me.

### Requirements - Skills:
A high degree of willingness to troubleshoot, tinker with values in .py files (General Python proficiency should not be required).
Probably either proficiency with Linux and CLI or willingness to learn a bit. Having some knowledge of docker is needed.
Reasonably seasoned in Home Assistant Automations
ESPHome basic knowledge is needed.

### Requirements - Software:
Samba and ESPHome addons installed on Home Assistant machine.
Ability to run a docker container with Python 3.11 on the same network. Note: Appears to not be compatible with Alpine-based containers currently, due to libraries not being supported.

### ESPMeter Process Flow
The main challenge in the project has been that ESPHome does not have an easy way to only trigger capturing an image on the camera at certain points in time. It's either a video or photo stream. This is inefficient in terms of energy, but also leads to unnecessary wear on the hardware, especially the LEDS used to ensure good lighting. As a result there is a strong integration with a home assistant automation to manage the capture of photos and sending the ESPHome unit to deep sleep.

The process flow is currently as follows:

1) Simple ESP32Cam created in ESPHome unit wakes up. Switches on lights for camera and after a short moment to ensure that everything is powered on, sends a message to Home assistant statig it is ready through a template switch.
2) A Home Assistant Automation picks up the ready state. It then proceeds with the following steps (see also example yaml):
   a) Switch on the lights on the ESP32Cam in case they are not.
   b) Wait 3 seconds for the lights to be fully on
   c) Send "Take snapshot" command and save file to home assistant device. This is currently done twice with a 3 second delay in between, because the first image tends to not be well lit, despite the long time for the camera and lights to be ready.
   d) Delay 10 seconds
   e) Publish MQTT message to the ESPMeter script to notify that a captured image is ready
   f) Wait 5 seconds
   g) Publish a new MQTT message to say there is no new image.
   h) Flip a switch on the ESP32Cam unit to trigger deep sleep (length determines resolution of final data). When ever updates needs to be made, this last automation step can be deactivated in Home Assistant so the ESP32Cam unit does not go to sleep, and is thus available for updates etc.
3) The ESPMeter script receives the "ready" MQTT message.
4) The ESPMeter script uses a samba client to retrieve the image and proceeds to extract the number from the image.
5) Afterwards a copy of the final result is stored back on the home assistant server. This is available for trouble shooting issues
6) The result along with confidence is sent to Home assistant. The raw value and confidence is always sent for debugging purposes. If confidence is low, a "final result" is not given, to avoid the data being all over the place in the statistics.
7) the ESPMeter script goes to sleep, waking up once a minute to check for a ready message by MQTT.

### Setup
The file setup_ocr_values.py can be run to quickly check the file loading and adjust the Region of Interest which is the part of the image parsed to EasyOCR for digit extraction.
The script should run in a venv with the requirement.txt dependencies installed. A subfolder /data with two subfolders /raw and /final are needed to save images. Images stored here are currently not automatically purged, so over time this needs to be done manually. They are retained for debugging purposes for now. The image files on the home assistant server are overwritten by new images so storage constraints are not an issue there.

### Would be nice to have in future:
Refactor to make a setup file with all variables
Make a simple webbased tool useful for finding the correct values for region of interest size and and brightness/contrast settings.
Premade dockerfile for easy setup, Home Assistant addon container, or other more elegant solution.

   
