# Sainlogic Weather Sensor Reverse Engineering Project

This repo has the code for my very extended reverse engineering effort for the Sainlogic WS-0835 weather station.

For a more detailed breakdown of this project, see the blog post <https://www.robopenguins.com/weather-station/>

Broadly this effort had two parts:
  1. Log data with an SDR and reverse engineer the 433MHz wireless protocol
  2. Tap into the data received at the display and publish it over WiFi

# SDR Effort

I logged the 433.92MHz transmissions with and SDR and created the `sdr_analysis1` and `sdr_analysis1` notebooks to capture the analysis.

I ended up figuring out most of the fields as covered in the blog post.

I then created the GNURadio module in `gr-sainlogic` to decode the data in realtime.

# Display WiFi Mod

See <https://www.robopenguins.com/weather-station/> for details, but I connected a NodeMCU WiFi board to the data stream received by the weather station display.

The `firmware` is the PlatformIO project for capturing the data and publishing it over MQTT.

I then created the scripts in `client` to log the results and publish them to Weather Underground.
