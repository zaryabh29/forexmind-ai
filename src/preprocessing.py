import pandas as pd
import numpy as np

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw OHLC candle dataframe.
    """
    df = df.copy()
    
    # Standardize column names
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Ensure datetime format
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
    
    # Drop duplicates by time
    df = df.drop_duplicates(subset=['time']).reset_index(drop=True)
    
    # Ensure numeric types
    for col in ['open', 'high', 'low', 'close', 'tick_volume', 'spread']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Drop invalid price rows
    df = df.dropna(subset=['open', 'high', 'low', 'close']).reset_index(drop=True)
    
    # Tag Trading Sessions (UTC assumed)
    df = add_session_features(df)
    return df

def add_session_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tags market session: Asian (00-08), London (08-16), New York (13-21), Overlap (13-16).
    """
    if 'time' not in df.columns:
        return df
        
    hours = df['time'].dt.hour
    
    df['hour'] = hours
    df['day_of_week'] = df['time'].dt.dayofweek
    
    # Session indicators
    df['is_asian'] = ((hours >= 0) & (hours < 8)).astype(int)
    df['is_london'] = ((hours >= 8) & (hours < 16)).astype(int)
    df['is_ny'] = ((hours >= 13) & (hours < 21)).astype(int)
    df['is_overlap'] = ((hours >= 13) & (hours < 16)).astype(int)
    
    return df
