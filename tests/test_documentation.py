import sys
import os
sys.path.append(os.path.join(os.path.dirname(sys.path[0]), 'src', 'continuous_futures'))
from continuous_futures import create_continuous_contract
import pandas as pd

def test_documentation():

    #  CODE STARTS HERE
    contract1 = pd.DataFrame([
        ['2023-01-01', 15.2, 13.8, 128, '2023F'],
        ['2023-01-02', 15.1, 13.9, 133, '2023F'],
        ['2023-01-03', 14.8, 14.1, 125, '2023F'],
    ], columns=['Date', 'Open', 'Close', 'Volume', 'Contract'])

    contract2 = pd.DataFrame([
        ['2023-01-02', 15.0, 13.2, 129, '2023G'],
        ['2023-01-04', 14.0, 13.1, 130, '2023G'],
        ['2023-01-05', 14.2, 14.0, 140, '2023G'],
    ], columns=['Date', 'Open', 'Close', 'Volume', 'Contract'])

    merged = pd.concat([contract1, contract2])

    continuous = create_continuous_contract(merged, 'Date', 'Volume', 'Contract', ['Open', 'Close'], ['Open'])
    #  CODE ENDS HERE


    expectation = pd.DataFrame([
        ['2023-01-01', 14.780690, 13.8, 128, '2023F'],
        ['2023-01-02', 14.683448, 13.9, 133, '2023F'],
        ['2023-01-04', 14.000000, 13.1, 130, '2023G'],
        ['2023-01-05', 14.200000, 14.0, 140, '2023G'],
    ], columns=['Date', 'Open', 'Close', 'Volume', 'Contract'], index=[0, 1, 4, 5])

    try:
        pd.testing.assert_frame_equal(continuous, expectation)
    except AssertionError:
        assert False, 'Exception not met'
