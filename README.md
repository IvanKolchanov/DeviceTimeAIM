# DeviceTimeAIM

Was used on the AIM Project at the University of Alabama.
Solves an issue of measuring time really accurately on an embedded device that returns time with accuracy of seconds.

By using binary search, by sequentually connecting to the device, asking time and accurately measuring objective global time. We can narrow down at which number of miliseconds does the number of seconds tick over, because the firmware at the time didn't provide that accuracy required for time drift testing.

The program worked successfully to measure the time drift in AIM devices over the course of multiple weeks. The average time drift was found to be similar between devices, so we were able to significantly reduce time drift by adjusting by the same average value on all devices.

Results can be tracked in the Excel Table provided, the Uncalibrated was done on 8 devices previous to any adjustments. The Calibrated was measured after the same devices were adjusted to -0.916 seconds/hr or 255ppm, the result was an imporvement from an error of 0.9159 s/h to 0.012 s/h with the testing that lasted 2 weeks, overall imporvement of 76 times.

Uncalibrated:
<img width="2286" height="1254" alt="image" src="https://github.com/user-attachments/assets/d84ea9a4-67cb-460b-b5c1-e177a753c34f" />

Calibrated:
<img width="2299" height="1237" alt="image" src="https://github.com/user-attachments/assets/c54e9edd-b3ec-4b51-9567-741da0d9ad41" />
