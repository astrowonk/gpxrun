# Gpx Run - Analyze GPX files for pace/distance/time

This class and utilities `gpxcsv` to convert to gpx files to pandas dataframes and perform simple analysis of speed,pace,time. It uses a rolling 5 second sum by default
to compute pace and speed (rather than just two adjacent points which are often 1 second apart)

```
g = GpxRun('2021-07-28-080242-Running-Who watches the watchers.gpx.gz')
#summary frame of 1 row
g.summary_data

#gpxcsv data frame augmented with computed rows
g.gpx_data
```

Example image of an apparently painfully slow run:

<img width="1109" alt="Screen Shot 2021-07-31 at 6 07 44 PM" src="https://user-images.githubusercontent.com/13702392/127753435-a4d9196f-3361-48f3-8925-337328798fa2.png">
