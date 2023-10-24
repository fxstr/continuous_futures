# Intro

Takes a DataFrames containing information for multiple future contracts and creates a
corresponding continuous contract (ratio back-adjusted, on highest volume).

## Installation

Use `pip install continuous_futures`

## Example

```python
from continuous_futures import create_continuous_contract
import pandas as pd

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
```

## Parameters

- data: DataFrame
    Order must be chronological: first by contract, then by date. Oldest date of oldest
    contract first. Must contain all columns whose names are passed to this function as
    parameters.
- date_column_name: str
    Name of the column that contains the date
- volume_column_name: str
    Name of the column that contains the volume; used to determine rollovers (on highest
    volume)
- contract_column_name: str
    Name of the column that contains the contract name; used determine where contracts
    change within the DataFrame
- adjustment_factor_columns_names: list of str
    Names of the columns to calculate the ratio from; usually only ['close']; if multiple
    are passed, their mean is used.
- adjustment_column_names: list of str
    Names of the columns to adjust by the ratio on rollovers.
