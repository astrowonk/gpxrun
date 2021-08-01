# Gpx Run - Analyze GPX files for pace/distance/time

This modules uses `gpxcsv` to convert to gpx files to pandas dataframes and perform simple analysis of speed,pace,time. It uses a rolling 5 second sum by default
to compute pace and speed (rather than just two adjacent points which are often 1 second apart)

## Install 

```python
git clone https://github.com/astrowonk/gpxrun.git
cd gpxcsv
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

