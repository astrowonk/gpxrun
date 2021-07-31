from gpxcsv import gpxtolist
import pandas as pd
import haversine as hs
import numpy as np
import glob


class GpxRun():
    """Class that analyzes GPX workout/run data"""
    gpx_data = None
    silent = False

    def __init__(self, file_path, silent=False) -> None:
        self.file_path = file_path
        self.silent = silent
        self.get_gpx_data(file_path)
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
        self.gpx_data['time'] = pd.to_datetime(self.gpx_data['time'])

    def analyze_gpx_data(self, rolling_window_size=5):
        self.gpx_data['lagged_ele'] = self.gpx_data['ele'].shift(1)
        self.gpx_data['lagged_lat'] = self.gpx_data['lat'].shift(1)
        self.gpx_data['lagged_lon'] = self.gpx_data['lon'].shift(1)
        self.gpx_data['lagged_time'] = self.gpx_data['time'].shift(1)
        self.gpx_data['ele_change_from_last_point'] = self.gpx_data[
            'ele'] - self.gpx_data['lagged_ele']
        total_elevation_change = np.abs(
            self.gpx_data['ele_change_from_last_point']).sum()
        self.gpx_data['great_circle_distance_from_last_point'] = self.gpx_data[
            ['lat', 'lon', 'lagged_lat',
             'lagged_lon']].apply(lambda x: hs.haversine(
                 (x[0], x[1]), (x[2], x[3]), unit=hs.Unit.METERS),
                                  axis=1)
        self.gpx_data['distance_from_last_point'] = np.sqrt(
            self.gpx_data['great_circle_distance_from_last_point']**2 +
            self.gpx_data['ele_change_from_last_point']**2)
        self.gpx_data['time_from_last_point'] = self.gpx_data[[
            'time', 'lagged_time'
        ]].apply(lambda x: (x[0] - x[1]).total_seconds(), axis=1)
        self.gpx_data['computed_rolling_speed'] = self.gpx_data[
            'distance_from_last_point'].rolling(rolling_window_size).sum(
            ) / self.gpx_data['time_from_last_point'].rolling(
                rolling_window_size).sum()
        self.gpx_data['mile_pace_rolling'] = 26.8224 / self.gpx_data[
            'computed_rolling_speed']
        self.run_mile_pace = 26.8224 / (
            self.gpx_data['distance_from_last_point'].sum() /
            self.gpx_data['time_from_last_point'].sum())

        total_distance_meters = self.gpx_data['distance_from_last_point'].sum()
        self.silent_print("*" * 40)
        self.silent_print(f"Run Start Time {self.gpx_data['time'].iloc[0]}")
        self.silent_print(
            f"Total Distance: {total_distance_meters:.2f} meters. {(total_distance_meters / 1609.34):.2f} miles."
        )
        total_time_dec_min = self.gpx_data['time_from_last_point'].sum() / 60
        total_time_min, total_time_sec = self.decimal_minutes_to_minutes_seconds(
            total_time_dec_min)
        self.silent_print(
            f"Total time: {total_time_min}\' {total_time_sec:.2f}\"")
        self.silent_print(
            f'Total pace: {self.decimal_minutes_to_formatted_string(self.run_mile_pace)}" min/mile'
        )  #copilot thanks

        #can we do splits
        # we need cummulative sum distance in miles
        self.gpx_data['cummulative_sum_distance'] = self.gpx_data[
            'distance_from_last_point'].cumsum()
        self.gpx_data['cummulative_sum_time'] = self.gpx_data[
            'time_from_last_point'].cumsum()
        self.gpx_data['cummulative_sum_distance_miles'] = self.gpx_data[
            'cummulative_sum_distance'] / 1609.34
        self.gpx_data['cummulative_sum_distance_miles'].fillna(0, inplace=True)

        self.gpx_data['mile_int'] = np.floor(
            self.gpx_data['cummulative_sum_distance_miles']) + 1.0

        out = self.gpx_data.groupby('mile_int')[[
            'time', 'cummulative_sum_distance_miles'
        ]].agg(['max', 'min'])
        out.columns = ['_'.join(x) for x in out.columns]
        res = ((out['time_max'] -
                out['time_min']).apply(lambda x: x.total_seconds()) /
               (out['cummulative_sum_distance_miles_max'] -
                out['cummulative_sum_distance_miles_min']) / 60).to_dict()
        self.silent_print("-" * 40)
        self.silent_print("Splits:")
        for key, val in res.items():
            self.silent_print(
                f'{int(key)} mile split: {self.decimal_minutes_to_formatted_string(val)}'
            )
        update_dict = {f"mile_{key}_split": val for key, val in res.items()}
        res_dict = {
            "start_time": self.gpx_data['time'].min(),
            'total_time_minutes': total_time_dec_min,
            'pace_mile': self.run_mile_pace,
            "total_distance_meters": total_distance_meters,
            "sum_abs_elevation_change_meters": total_elevation_change,
        }
        res_dict.update(update_dict)
        self.summary_data = pd.DataFrame([res_dict])


def gpx_multi(input, silent=True):
    """Process glob of input and concat summary data from GpxRun class"""
    gpx_runs = []
    for f in glob.glob(input):
        gpx_runs.append(GpxRun(f, silent=silent))
    gpx_runs = pd.concat([x.summary_data for x in gpx_runs])
    return gpx_runs
