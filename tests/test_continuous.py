import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(sys.path[0]), 'src', 'continuous_futures'))
import continuous_futures


def get_test_data():
    # Use K on 06; use J on 05, 04; use H on 03, 02, 01
    # On 5th, K is 7/8, J is 6/7; factor is 7.5 / 6.5 = 1.15384615
    # On 3rd, J is 5/5, H is 6/6; factor is 0.83333333, multiplied with previous: 0.96153845
    
    # Contains test for 
    # - change on same volume (2022-03-03 to 2023H)
    columns = ['Date', 'Contract', 'Open', 'Close', 'Irrelevant', 'Volume']
    data = pd.DataFrame([
        ['2022-03-01', '2023H', 5, 6, 2, 110], # ← this
        ['2022-03-02', '2023H', 6, 8, 2, 107], # ← this
        ['2022-03-03', '2023H', 6, 6, 2, 110], # ← this (same volume)
        ['2022-03-04', '2023H', 6, 5, 2, 101],
        ['2022-03-05', '2023H', 3, 4, 1, 102],
        ['2022-03-01', '2023J', 6, 7, 2, 105],
        ['2022-03-02', '2023J', 5, 6, 2, 106],
        ['2022-03-03', '2023J', 5, 5, 2, 110],
        ['2022-03-04', '2023J', 4, 5, 2, 109], # ← this
        ['2022-03-05', '2023J', 6, 7, 2, 114], # ← this
        ['2022-03-06', '2023J', 6, 8, 2, 111],
        ['2022-03-02', '2023K', 6, 8, 2, 100],
        ['2022-03-03', '2023K', 5, 6, 2, 102],
        ['2022-03-04', '2023K', 5, 6, 2, 110],
        ['2022-03-05', '2023K', 7, 8, 2, 112],
        ['2022-03-06', '2023K', 8, 8, 2, 113], # ← this
    ], columns=columns)
    print('data\n', data)
    return data

def get_basic_expectation():
    columns = ['Date', 'Contract', 'Open', 'Close', 'Irrelevant', 'Volume']
    basic_expectation = pd.DataFrame([
        ['2022-03-01', '2023H', 5, 5.769230, 2, 110],
        ['2022-03-02', '2023H', 6, 7.692307, 2, 107],
        ['2022-03-03', '2023H', 6, 5.769230, 2, 110],
        ['2022-03-04', '2023J', 4, 5.769230, 2, 109],
        ['2022-03-05', '2023J', 6, 8.0769231, 2, 114],
        ['2022-03-06', '2023K', 8, 8, 2, 113],
    ], columns=columns, index=[0, 1, 2, 8, 9, 15])
    return basic_expectation



def test_basic_continuous():
    result = continuous_futures.create_continuous_contract(get_test_data(), 'Date', 'Volume', 'Contract', ['Open', 'Close'], ['Close'])
    try:
        pd.testing.assert_frame_equal(result, get_basic_expectation())
    except AssertionError:
        assert False, 'Exception not met'


def test_basic_multiple_adjustment_columns():
    result = continuous_futures.create_continuous_contract(get_test_data(), 'Date', 'Volume', 'Contract', ['Open', 'Close'], ['Close', 'Open'])
    columns = ['Date', 'Contract', 'Open', 'Close', 'Irrelevant', 'Volume']
    expectation = pd.DataFrame([
        ['2022-03-01', '2023H', 4.80769225, 5.769230, 2, 110],
        ['2022-03-02', '2023H', 5.7692307, 7.692307, 2, 107],
        ['2022-03-03', '2023H', 5.7692307, 5.769230, 2, 110],
        ['2022-03-04', '2023J', 4.6153846, 5.769230, 2, 109],
        ['2022-03-05', '2023J', 6.9230769, 8.0769231, 2, 114],
        ['2022-03-06', '2023K', 8, 8, 2, 113],
    ], columns=columns, index=[0, 1, 2, 8, 9, 15])

    try:
        pd.testing.assert_frame_equal(result, expectation)
    except AssertionError:
        assert False, 'Exception not met'


def test_continuous_with_missing_rollover_info():
    """
    On rollover date, younger contract does not contain rollover information; adjustment factor
    cannot be calculated
    """
    data = get_test_data()
    # Drop data for rollover on -03 to 2023H
    data = data.drop([7])
    result = continuous_futures.create_continuous_contract(data, 'Date', 'Volume', 'Contract', ['Open', 'Close'], ['Close'])
    columns = ['Date', 'Contract', 'Open', 'Close', 'Irrelevant', 'Volume']
    expectation = pd.DataFrame([
        ['2022-03-01', '2023H', 5, 5.43956046, 2, 110],
        # Contract switch now happens on 2nd instead of 3rd because younger contract data is
        # missing on 3rd
        # 2023J is 5/6 = 5.5, 2023H is 6/8 = 7, factor is 0.78571429, absolute 0.90659341
        ['2022-03-02', '2023H', 6, 7.25274728, 2, 107],
        # On 3rd, there's no data: Old contract data is missing, and we can not switch to the new one
        # because we don't have the rollover info
        ['2022-03-04', '2023J', 4, 5.769230, 2, 109],
        ['2022-03-05', '2023J', 6, 8.0769231, 2, 114],
        ['2022-03-06', '2023K', 8, 8, 2, 113],
        # index: 7 is missing, index will be re-created and 7 will be used
    ], columns=columns, index=[0, 1, 7, 8, 14])

    try:
        pd.testing.assert_frame_equal(result, expectation)
    except AssertionError:
        assert False, 'Exception not met'



def test_continuous_with_older_date_missing():
    data = get_test_data()
    # Drop data for older contract 2023H -02 when -02 exists on younger contracts (2023J)
    data = data.drop([1])
    result = continuous_futures.create_continuous_contract(data, 'Date', 'Volume', 'Contract', ['Open', 'Close'], ['Close'])
    columns = ['Date', 'Contract', 'Open', 'Close', 'Irrelevant', 'Volume']
    expectation = pd.DataFrame([
        ['2022-03-01', '2023H', 5, 5.769230, 2, 110],
        ['2022-03-03', '2023H', 6, 5.769230, 2, 110],
        ['2022-03-04', '2023J', 4, 5.769230, 2, 109],
        ['2022-03-05', '2023J', 6, 8.0769231, 2, 114],
        ['2022-03-06', '2023K', 8, 8, 2, 113],
        # Index: 1 is missing, index will be re-created and 1 will be used
    ], columns=columns, index=[0, 1, 7, 8, 14])

    try:
        pd.testing.assert_frame_equal(result, expectation)
    except AssertionError:
        assert False, 'Exception not met'


def test_continuous_with_non_unique_indexes():
    data = get_test_data()
    # If a user imports every contract from a different CSV file, indexes might not be unique.
    # Test if code still works under those circumstances.
    data.index = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5]
    result = continuous_futures.create_continuous_contract(data, 'Date', 'Volume', 'Contract', ['Open', 'Close'], ['Close'])
    
    try:
        pd.testing.assert_frame_equal(result, get_basic_expectation())
    except AssertionError:
        assert False, 'Exception not met'

