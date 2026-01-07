"""
Script to merge all labeled data CSVs and synthetic data into one training dataset.
"""

import pandas as pd
import os

def merge_datasets():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Labeled data files
    labeled_files = [
        'akbnk_labeled_data.csv',
        'bist100_labeled_data.csv',
        'eregl_labeled_data.csv',
        'garan_labeled_data.csv',
        'kchol_labeled_data.csv',
        'thyao_labeled_data.csv',
        'usdtry_labeled_data.csv',
        'xagtry_labeled_data.csv',
        'xautry_labeled_data.csv',
    ]
    
    # Synthetic data file
    synthetic_file = 'syntetic_comments.csv'
    
    all_dfs = []
    
    print("Merging datasets...")
    print("-" * 60)
    
    # Load labeled data
    for filename in labeled_files:
        file_path = os.path.join(base_dir, filename)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['source'] = filename.replace('_labeled_data.csv', '')
            all_dfs.append(df)
            print(f"  {filename}: {len(df)} rows")
        else:
            print(f"  {filename}: NOT FOUND")
    
    # Load synthetic data
    synthetic_path = os.path.join(base_dir, synthetic_file)
    if os.path.exists(synthetic_path):
        df_syn = pd.read_csv(synthetic_path)
        df_syn['source'] = 'synthetic'
        all_dfs.append(df_syn)
        print(f"  {synthetic_file}: {len(df_syn)} rows")
    else:
        print(f"  {synthetic_file}: NOT FOUND")
    
    # Merge all
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Save merged dataset
    output_path = os.path.join(base_dir, 'training_data.csv')
    merged_df.to_csv(output_path, index=False)
    
    print("-" * 60)
    print(f"TOTAL: {len(merged_df)} rows")
    print(f"Saved to: training_data.csv")
    
    # Show label distribution
    print("\nLabel Distribution:")
    print(merged_df['label'].value_counts().to_string())
    
    # Show source distribution
    print("\nSource Distribution:")
    print(merged_df['source'].value_counts().to_string())


if __name__ == '__main__':
    merge_datasets()
