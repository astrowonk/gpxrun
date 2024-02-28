from gpxcsv import gpxtolist
import pandas as pd
import haversine as hs
import numpy as np
import argparse
import glob
import datetime

__VERSION__ = '0.8.5'


class GpxRun():
    """Class that analyzes GPX workout/run data"""
    gpx_data = None
    silent = False
    time_col = None
    rolling_window_size = None

    def __init__(self,
                 file_path,
                 silent=False,
                 time_col='time',
                 rolling_window_size=5) -> None:
        """Rolling window size only changes mile_pace_rolling and computer_rolling_speed. Summary stats are based on
        cummulative sums and are uneffected by the rolling parameter."""
        self.file_path = file_path
        self.silent = silent
        self.rolling_window_size = rolling_window_size
        self.time_col = time_col
        self.get_gpx_data(file_path)
        assert self.time_col in self.gpx_data.columns, f"{time_col} must be in gpx data columns. Specify alternative time column name."
        self.summary_data = pd.DataFrame()
        self.analyze_gpx_data()

    def silent_print(self, s):
        if not self.silent:
            print(s)

    @staticmethod
    def decimal_minutes_to_minutes_seconds(decimal_minutes):
        """Take decimal minutes and return minutes and decimmal seconds"""
        minutes = int(decimal_minutes)
        decimal_seconds = (decimal_minutes - minutes) * 60
        return minutes, decimal_seconds

    @staticmethod
    def decimal_minutes_to_formatted_string(decimal_minutes):
        """Take decimal minutes and return formatted string"""
        minutes, decimal_seconds = GpxRun.decimal_minutes_to_minutes_seconds(
            decimal_minutes)
        return f'{str(minutes):>2}\' {decimal_seconds:.1f}"'

    def get_gpx_data(self, file_path):
        self.gpx_data = pd.DataFrame(gpxtolist(file_path))
        self.gpx_data[self.time_col] = pd.to_datetime(
            self.gpx_data[self.time_col])
        self.gpx_data.sort_values(by=self.time_col, inplace=True)

    def analyze_gpx_data(self):
        if not all(x in self.gpx_data.columns
                   for x in ['lat', 'lon', 'ele', 'time']):
            print("Not processing, missing lat, lon, ele, or time columns")
            return
        self.gpx_data['lagged_ele'] = self.gpx_data['ele'].shift(1)
        self.gpx_data['lagged_lat'] = self.gpx_data['lat'].shift(1)
        self.gpx_data['lagged_lon'] = self.gpx_data['lon'].shift(1)
        self.gpx_data['lagged_time'] = self.gpx_data[self.time_col].shift(1)
        self.gpx_data['ele_change_from_last_point'] = self.gpx_data[
            'ele'] - self.gpx_data['lagged_ele']
        total_elevation_change = np.abs(
            self.gpx_data['ele_change_from_last_point']).sum()
        self.gpx_data['great_circle_distance_from_last_point'] = self.gpx_data[
            ['lat', 'lon', 'lagged_lat',
             'lagged_lon']].apply(lambda x: hs.haversine(
                 (x.iloc[0], x.iloc[1]), (x.iloc[2], x.iloc[3]), unit=hs.Unit.METERS),
                                  axis=1)
        self.gpx_data['distance_from_last_point'] = np.sqrt(
            self.gpx_data['great_circle_distance_from_last_point']**2 +
            self.gpx_data['ele_change_from_last_point']**2)
        self.gpx_data['time_from_last_point'] = self.gpx_data[[
            self.time_col, 'lagged_time'
        ]].apply(lambda x: (x.iloc[0] - x.iloc[1]).total_seconds(), axis=1)
        self.gpx_data['computed_rolling_speed'] = self.gpx_data[
            'distance_from_last_point'].rolling(self.rolling_window_size).sum(
            ) / self.gpx_data['time_from_last_point'].rolling(
                self.rolling_window_size).sum()
        self.gpx_data['mile_pace_rolling'] = 26.8224 / self.gpx_data[
            'computed_rolling_speed']
        self.run_mile_pace = 26.8224 / (
            self.gpx_data['distance_from_last_point'].sum() /
            self.gpx_data['time_from_last_point'].sum())

        total_distance_meters = self.gpx_data['distance_from_last_point'].sum()

        total_time_dec_min = self.gpx_data['time_from_last_point'].sum() / 60
        total_time_min, total_time_sec = self.decimal_minutes_to_minutes_seconds(
            total_time_dec_min)

        #can we do splits
        # we need cummulative sum distance in miles
        self.gpx_data['cummulative_sum_distance'] = self.gpx_data[
            'distance_from_last_point'].cumsum()
        self.gpx_data['cummulative_sum_time'] = self.gpx_data[
            'time_from_last_point'].cumsum()
        self.gpx_data['cummulative_sum_distance_miles'] = self.gpx_data[
            'cummulative_sum_distance'] / 1609.344
        self.gpx_data.fillna({'cummulative_sum_distance_miles':0}, inplace=True)

        self.gpx_data['mile_int'] = np.floor(
            self.gpx_data['cummulative_sum_distance_miles']) + 1.0

        out = self.gpx_data.groupby('mile_int')[[
            self.time_col, 'cummulative_sum_distance_miles'
        ]].agg(['max', 'min'])
        out.columns = ['_'.join(x) for x in out.columns]
        res = (
            (out[f'{self.time_col}_max'] -
             out[f'{self.time_col}_min']).apply(lambda x: x.total_seconds()) /
            (out['cummulative_sum_distance_miles_max'] -
             out['cummulative_sum_distance_miles_min']) / 60).to_dict()

        update_dict = {f"mile_{key}_split": val for key, val in res.items()}
        res_dict = {
            "start_time":
            self.gpx_data[self.time_col].min().to_pydatetime().replace(
                tzinfo=datetime.timezone.utc).astimezone(),
            'total_time_minutes':
            total_time_dec_min,
            'pace_mile':
            self.run_mile_pace,
            'pace_mile_string':
            self.decimal_minutes_to_formatted_string(self.run_mile_pace),
            "total_distance_meters":
            total_distance_meters,
            "total_distance_miles":
            total_distance_meters / 1609.344,
            "sum_abs_elevation_change_meters":
            total_elevation_change,
        }
        res_dict.update(update_dict)
        if 'type' in self.gpx_data.columns:
            res_dict.update({"type": self.gpx_data['type'].iloc[0]})
        if 'hAcc' in self.gpx_data.columns:
            res_dict.update(
                {"avg_gps_accuracy_meters": self.gpx_data['hAcc'].mean()})
        self.summary_data = pd.DataFrame([res_dict])
        self.silent_print("*" * 40)
        self.silent_print(
            f"Run Start Time {res_dict['start_time'].strftime('%a %b %d %H:%m:%S %Z')}"
        )
        self.silent_print(
            f"Total Distance: {total_distance_meters:.2f} meters. {(total_distance_meters / 1609.344):.2f} miles."
        )
        self.silent_print(
            f"Total time: {total_time_min}\' {total_time_sec:.2f}\"")
        self.silent_print(
            f'Total pace: {self.decimal_minutes_to_formatted_string(self.run_mile_pace)}" min/mile'
        )  #copilot thanks
        if 'hAcc' in res_dict.keys():
            self.silent_print(
                f"Average GPS Accuracy {res_dict.get('avg_gps_accuracy_meters',0):.2f} meters"
            )
        self.silent_print("-" * 40)
        self.silent_print("Splits:")
        for key, val in res.items():
            self.silent_print(
                f'{int(key)} mile split: {self.decimal_minutes_to_formatted_string(val)}'
            )


def gpx_multi(input, silent=True, **kwargs):
    """Process glob of input and concat summary data from GpxRun class"""
    gpx_runs = []
    for f in glob.glob(input):
        print(f"Processing file {f}")
        gpx_runs.append(GpxRun(f, silent=silent, **kwargs))
    gpx_runs = pd.concat([x.summary_data
                          for x in gpx_runs]).sort_values('start_time')
    return gpx_runs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Process gpx files and output summary data')
    parser.add_argument('file', help='a gpx file to process')
    args = parser.parse_args()

    GpxRun(args.file, silent=False)
