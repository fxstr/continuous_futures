import pandas as pd
import numpy

def _get_rollover_indexes(data, date_column_name, volume_column_name, contract_column_name):
    """
    Returns all indexes on which rollovers should happen; the dates correspond to the first entry
    in the *previous* contract

    Parameters
    ----------
        data: DataFrame
            Order must be chronological: first by contract, then by date. Oldest date of oldest
            contract first. Must contain all columns whose names are passed as parameters. Oldest
            first to make sure we switch on previous contract if volume is equal.
        date_column_name: str
            Name of the column that contains the date
        volume_column_name: str
            Name of the column that contains the volume
        contract_column_name: str
            Name of the column that contains the contract name
    """
    
    # Get the index within continuous_data that has the highest volume per date. 
    volume_grouped = data.groupby(date_column_name, sort=False)[volume_column_name]

    # Convert to DataFrame in order to access row's index (name) when iterating with apply;
    # seems not to be possible with a Series
    highest_volume_indexes = pd.DataFrame(volume_grouped.idxmax())
    highest_volume_indexes_sorted_by_date = highest_volume_indexes.sort_values(by=date_column_name)

    # Remove all rollovers that would switch to younger contracts; to do so go through data
    # from the back (youngest date) and keep the smallest contract index (i.e. the oldest contract)
    rollover_dates = highest_volume_indexes_sorted_by_date.iloc[::-1]
    rollover_dates = rollover_dates.apply(lambda row: min(rollover_dates.loc[:row.name].values[:, 0]), axis=1)

    # Remove all rollovers that happen more than once on a contract
    deduped = data.loc[rollover_dates].drop_duplicates([contract_column_name])

    return deduped.iloc[::-1].index.tolist()



def create_continuous_contract(data, date_column_name, volume_column_name, contract_column_name, adjustment_factor_columns_names, adjustment_column_names):
    """ Create a continuous contract from multiple future contracts; uses rollover on highest
    volume and back-adjusts by product.
    
    Parameters
    ----------
        data: DataFrame
            Order must be chronological: first by contract, then by date. Oldest date of oldest
            contract first. Must contain all columns whose names are passed to this function
            as parameters.
        date_column_name: str
            Name of the column that contains the date
        volume_column_name: str
            Name of the column that contains the volume; used to determine rollovers (on highest
            volume)
        contract_column_name: str
            Name of the column that contains the contract name; used determine where contracts
            change within the DataFrame
        adjustment_factor_columns_names: list of str
            Names of the columns to calculate the ratio from; usually only ['close']; if multiple
            are passed, their mean is used.
        adjustment_column_names: list of str
            Names of the columns to adjust by the ratio on rollovers.
    """

    # We access data by index; therefore we must ensure those indices are unique. As we'll use 
    data_with_unique_index = data.copy().reset_index()
    data_with_unique_index.drop('index', axis=1, inplace=True)

    rollover_indexes = _get_rollover_indexes(data_with_unique_index, date_column_name, volume_column_name, contract_column_name)

    # Reverse order – because we back-adjust the contracts and e.g. rolling windows only work
    # from start to end
    reversed_data = data_with_unique_index.iloc[::-1].copy()
    reversed_data['AdjustmentFactorValue'] = reversed_data.loc[:, adjustment_factor_columns_names].mean(axis=1)

    rollovers = reversed_data.loc[rollover_indexes]
    rollover_dates = rollovers.loc[:, date_column_name].unique()

    dates = reversed_data.loc[:, date_column_name].unique()
    dates_sorted = numpy.sort(dates)[::-1]

    current_contract = reversed_data.loc[:, contract_column_name].iloc[0]
    next_contract = current_contract
    adjustment_factor = 1
    result = pd.DataFrame()

    for current_date in dates_sorted:

        # Is it a rollover date?
        if current_date in rollover_dates:
            rollover_data = rollovers[rollovers[date_column_name] == current_date]
            next_contract = rollover_data.loc[:, contract_column_name].iloc[0]

        # While a rollover is happening, next_contract is different from current_contract; handle
        # this separately from the exact rollover date to make sure we can rollover if there is no
        # data for the next contract on the current date
        if next_contract != current_contract:
            current_adjustment_value_row = reversed_data[(reversed_data[date_column_name] == current_date) & (reversed_data[contract_column_name] == current_contract)]
            next_adjustment_value_row = reversed_data[(reversed_data[date_column_name] == current_date) & (reversed_data[contract_column_name] == next_contract)]
            # Update adjustment_factor
            if len(current_adjustment_value_row) and len(next_adjustment_value_row):
                current_adjustment_value = current_adjustment_value_row.loc[:, 'AdjustmentFactorValue'].iloc[0]
                next_adjustment_value = next_adjustment_value_row.loc[:, 'AdjustmentFactorValue'].iloc[0]
                current_adjustment_factor = current_adjustment_value / next_adjustment_value
                adjustment_factor = adjustment_factor * current_adjustment_factor
                current_contract = next_contract

        current_row = reversed_data[(reversed_data[date_column_name] == current_date) & (reversed_data[contract_column_name] == current_contract)]
        
        # There's no data for the current date (i.e. not for the current contract): Advance to
        # next date
        if (len(current_row) > 0):
            current_index = current_row.index
            adjusted_data = data_with_unique_index.loc[current_index]
            adjusted_data.loc[:, adjustment_column_names] = adjusted_data.loc[:, adjustment_column_names] * adjustment_factor
            result = pd.concat([result, adjusted_data])
        
    return result.iloc[::-1].copy()