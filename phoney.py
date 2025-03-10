import pandas as pd

data = {
    "Happiness": ['0-1 Hours', '1-3 Hours', '3-5 Hours', '5-7 Hours', '7-9 Hours', '9-11 Hours'],
    "Quantity of Students": [0, 3, 2, 3, 0, 1]
}    
df = pd.DataFrame(data)

print(df['Quantity of Students'])


maxLength = max(len(df['Happiness'][i] for i in range(len(df['Happiness']))))

print(maxLength)