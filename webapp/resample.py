import pandas as pd


def resample(series, start, end, frequency, filling='raise'):
    """
    Resample a time series

    This method takes a time series from `old_start` to `old_end` (frequency
    non-necessarily constant) and produces a time series from `start` to `end`
    with frequency `frequency`, by interpolating the old values.

    When `start` < `old_start` or `end` > `old_end`, the behaviour is specified
    using the `filling` argument:
    - 'raise' will raise an IndexError exception
    - 'nan' will fill the values outside the original interval with NaNs
    - 'constant' will fill the values outside the original interval with the
      closest values
    """

    old_start = series.index[0]
    old_end = series.index[-1]

    new_index = pd.date_range(start=start, end=end, freq=frequency)
    new_values = []

    if filling == 'raise':
        if start < old_start or end > old_end:
            raise IndexError(
                "Cannot resample from (%r -> %r) to (%r -> %r)"
                % (old_start, old_end, start, end))
    elif filling == 'nan':
        fill_before = fill_after = float('nan')
    elif filling == 'constant':
        fill_before = series.ix[0]
        fill_after = series.ix[-1]
    else:
        raise ValueError("Unknown filling method '%r'" % filling)

    # Interpolate data
    step = 0

    for t in new_index:
        if old_start <= t <= old_end and start <= t <= end:
            while t > series.index[step]:
                if step + 1 < len(series.index):
                    step += 1
                else:
                    break

            if step == 0:
                # You are between timeOld[0] and timeOld[1]
                # Forward interpolation:
                t_prev = series.index[step].timestamp()
                t_next = series.index[step + 1].timestamp()

                y_prev = series.ix[step]
                y_next = series.ix[step + 1]

                y = ((((y_next - y_prev) / (t_next - t_prev)) *
                     (t.timestamp() - t_prev)) + y_prev)
                new_values.append(y)

            elif step > 0:
                # You are between timeOld[step - 1] and timeOld[step]
                # Backward interpolation:
                t_prev = series.index[step - 1].timestamp()
                t_next = series.index[step].timestamp()

                y_prev = series.ix[step - 1]
                y_next = series.ix[step]

                y = ((((y_next - y_prev) / (t_next - t_prev)) *
                     (t.timestamp() - t_prev)) + y_prev)
                new_values.append(y)
        elif t < old_start:
            new_values.append(fill_before)
        elif t > old_end:
            new_values.append(fill_after)

    interpolated = pd.Series(index=new_index, data=new_values)

    return interpolated


if __name__ == '__main__':
    import pylab as pl
    import datetime

    timestamps = [1462170741, 1462170763, 1462170783, 1462170799]
    index = pd.to_datetime(timestamps, unit='s')
    data = [57, 24, 40, 27]
    start = datetime.datetime.strptime(
        "2016-05-02 06:31:30", "%Y-%m-%d %H:%M:%S")
    end = datetime.datetime.strptime(
        "2016-05-02 06:34:10", "%Y-%m-%d %H:%M:%S")
    frequency = '5s'
    series = pd.Series(data=data, index=index)

    for filling in ['raise', 'nan', 'constant']:

        try:
            interpolated = resample(series, start, end, frequency, filling)
        except IndexError:
            interpolated = pd.Series(index=index)

        _, ax = pl.subplots(1)

        series.plot(ax=ax, style='ks:')
        interpolated.plot(ax=ax, style='ro')

        ax.set_title("Filling: %s" % filling)
        ax.legend(['Original', 'Resampled'])

    pl.show()
