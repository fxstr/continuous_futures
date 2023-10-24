import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(sys.path[0]), 'src', 'continuous_futures'))
import continuous_futures


def test_regular_rollover_indexes():
    data = pd.DataFrame([
        ['2022-03-01', 'H', 5],
        ['2022-03-02', 'H', 3],
        ['2022-03-02', 'J', 5],
    ], columns=['Date', 'Contract', 'Volume'])
    result = continuous_futures._get_rollover_indexes(data, 'Date', 'Volume', 'Contract')
    assert result == [0, 2]

def test_rollover_indexes_with_previous_higher():
    # Switch to H on 3rd; previous contract J has higher volume on 2nd
    data = pd.DataFrame([
        ['2022-03-01', 'H', 5],
        ['2022-03-02', 'H', 3],
        # Rollover onon 2022-03-03; but later contract has higher volume on 2022-03-02
        ['2022-03-03', 'H', 7],
        ['2022-03-02', 'J', 5],
        ['2022-03-03', 'J', 6],
    ], columns=['Date', 'Contract', 'Volume'])
    result = continuous_futures._get_rollover_indexes(data, 'Date', 'Volume', 'Contract')
    # index 2 is not part of result as we don't switch back
    assert result == [2]

def test_rollover_indexes_with_missing_data():
    data = pd.DataFrame([
        ['2022-03-01', 'H', 5],
        # No data for H on 2022-03-02
        ['2022-03-02', 'J', 3],
    ], columns=['Date', 'Contract', 'Volume'])
    result = continuous_futures._get_rollover_indexes(data, 'Date', 'Volume', 'Contract')
    # index 2 is not part of result as we don't switch back
    assert result == [0, 1]

def test_rollover_on_equal_volume():
    data = pd.DataFrame([
        ['2022-03-01', 'H', 3],
        # H has same volume as J on 2022-03-02: Rollover to H
        ['2022-03-01', 'J', 3],
    ], columns=['Date', 'Contract', 'Volume'])
    result = continuous_futures._get_rollover_indexes(data, 'Date', 'Volume', 'Contract')
    # index 2 is not part of result as we don't switch back
    assert result == [0]

def test_rollover_only_once_per_contract():
    data = pd.DataFrame([
        ['2022-03-01', 'H', 5],
        ['2022-03-02', 'H', 3],
        ['2022-03-02', 'J', 5],
        ['2022-03-03', 'J', 4],
        ['2022-03-04', 'J', 5],
    ], columns=['Date', 'Contract', 'Volume'])
    result = continuous_futures._get_rollover_indexes(data, 'Date', 'Volume', 'Contract')
    assert result == [0, 4]

def test_rollover_with_higher_indexes():
    # Order of dates and indexes of highest volume will be
    # 2022-03-05       3
    # 2022-03-03       1
    # 2022-03-04       7
    # 2022-03-06       9
    # 2022-03-02       5
    # If we don't sort by date, the result would be [1, 5] because 7 and 8 are higher numbers than
    # 5, while 3 is a higher number than 1
    data = pd.DataFrame([
        ['2022-03-05', '2023H', 102],
        ['2022-03-03', '2023J', 110],
        ['2022-03-04', '2023J', 109],
        ['2022-03-05', '2023J', 114], # ← this
        ['2022-03-06', '2023J', 111],
        ['2022-03-02', '2023K', 100],
        ['2022-03-03', '2023K', 102],
        ['2022-03-04', '2023K', 110],
        ['2022-03-05', '2023K', 112],
        ['2022-03-06', '2023K', 113], # ← this
    ], columns=['Date', 'Contract', 'Volume'])
    result = continuous_futures._get_rollover_indexes(data, 'Date', 'Volume', 'Contract')
    assert result == [3, 9]
