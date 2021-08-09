# Gpx Run - Analyze GPX files for pace/distance/time

This modules uses my [gpxcsv](https://pypi.org/project/gpxcsv/) module to convert to gpx files to pandas dataframes and perform simple analysis of speed, pace, and time. You can see it in action [via my web app](https://marcoshuerta.com/gpxrun/).

## Install 

```python
git clone https://github.com/astrowonk/gpxrun.git
cd gpxrun
python setup.py install
```

## Use

```
from gpxrun import GpxRun
g = GpxRun('myfile.gpx.gz')
#summary frame of 1 row
g.summary_data

#gpxcsv data frame augmented with computed rows
g.gpx_data
```

Example image of an apparently painfully slow run:

<img width="1109" alt="Screen Shot 2021-07-31 at 6 07 44 PM" src="https://user-images.githubusercontent.com/13702392/127753435-a4d9196f-3361-48f3-8925-337328798fa2.png">

Also includes a helper function `gpx_multi` which can process a glob of files and return a concattenated dataframe summary.

```python
df = gpx_multi('*.gpx')
```

## Wait, why do I look so much slower with this?

At least when it comes to the Apple Watch, pace/distance information shown in the Fitness app or during a workout is based on the __pedometer__, not the GPS. In theory, [the Watch calibrates itself](https://support.apple.com/en-us/HT204516) using the GPS so the pedometer is accurate. I know that I had disabled location services for **Motion Calibration and Distance**, and that when I finaly turned this on, suddenly the Watch started calibrating and within a run or two, it was telling me I was slower than I had been.

In practice with `gpxrun`, an uncalibrated Watch will have the largest discrepencies with the GPS-based pace/speed/distance, but this gap will close if/as it is calibrated. So far, in about a week of calibration, the self-reported distances from the Watch pedometer are about 2%-3% larger than what I find in the GPS data in the GPX exported files (using HealthFit[https://apps.apple.com/us/app/healthfit/id1202650514]).

How accurate is the pedometer can be when fully calibrated, I do not know yet. I will eventually update this readme comparing pace/distance data from `gpxrun` with what the pedometer-based distance iOS reports.

Another question, how accurate is GPS based pace/distance? The Watch reports GPS accuracy and it's +/- a meter or two. Presumably over a long run, the total integrated distance is fairly accurate.
