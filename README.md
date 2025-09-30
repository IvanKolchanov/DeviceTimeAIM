# DeviceTimeAIM

Was used on the AIM Project at the University of Alabama.
Solves an issue of measuring time really accurately on an embedded device that returns time with accuracy of seconds.

By using binary search, by sequentually connecting to the device, asking time and accurately measuring objective global time. We can narrow down at which number of miliseconds does the number of seconds tick over, because the firmware at the time didn't provide that accuracy required for time drift testing.

The program worked successfully to measure the time drift in AIM devices over the course of multiple weeks. The average time drift was found to be similar between devices, so we were able to significantly reduce time drift by adjusting by the same average value on all devices.

Results can be tracked in the Excel Table provided, the Uncalibrated was done on the devices previous to any adjustments. The Calibrated was measured after the device settings were adjusted to -0.916 seconds/hr or 255ppm, the result was an imporvement from an error of 0.9159 s/h to 0.012 s/h with the testing that lasted 2 weeks, overall imporvement of 76 times.
