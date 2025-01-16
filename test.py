import pandas as pd
import numpy as np

# Sample DataFrame
df = pd.DataFrame({
    'Age': [25, 30, 35, 40, 20]
})

# Defining conditions and corresponding labels
conditions = [
    (df['Age'] < 30),  # Condition for 'Young'
    (df['Age'] >= 30) & (df['Age'] < 40),  # Condition for 'Middle-aged'
    (df['Age'] >= 40)  # Condition for 'Old'
]

labels = ['Young', 'Middle-aged', 'Old']

# Adding a new column 'Category' with 3 different labels based on 'Age'
df['Category'] = np.select(conditions, labels)

print(df)

