import pandas as pd
import numpy as np
from datetime import datetime
import json

class EarthquakeDataCleaner:
    def __init__(self, input_file):
        self.input_file = input_file
        self.df = None
        self.original_df = None
        self.cleaning_report = {}
        self.validation_errors = []
        
    def load_data(self):
        """Load the CSV file into a pandas DataFrame"""
        print("Loading data...")
        self.df = pd.read_csv(self.input_file)
        self.original_df = self.df.copy()
        print(f"✓ Loaded {len(self.df)} records with {len(self.df.columns)} columns")
        return self.df
    
    def analyze_initial_issues(self):
        """Identify and report initial data quality issues"""
        print("\n" + "="*80)
        print("INITIAL DATA QUALITY ASSESSMENT")
        print("="*80)
        
        # Check dimensions
        print(f"\nDataset Dimensions:")
        print(f"  - Rows: {len(self.df)}")
        print(f"  - Columns: {len(self.df.columns)}")
        
        # Check for missing values
        print(f"\nMissing Values by Column:")
        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df) * 100).round(2)
        for col in self.df.columns:
            if missing[col] > 0:
                print(f"  - {col}: {missing[col]} ({missing_pct[col]}%)")
        
        # Check for duplicates
        print(f"\nDuplicate Analysis:")
        full_dupes = self.df.duplicated().sum()
        id_dupes = self.df.duplicated(subset=['id']).sum()
        print(f"  - Completely identical rows: {full_dupes}")
        print(f"  - Duplicate IDs: {id_dupes}")
        
        # Check data types
        print(f"\nData Types:")
        for col, dtype in self.df.dtypes.items():
            print(f"  - {col}: {dtype}")
    
    def clean_missing_values(self):
        """Handle missing values appropriately"""
        print("\n" + "="*80)
        print("HANDLING MISSING VALUES")
        print("="*80)
        
        issues_found = {}
        
        # Numeric columns - fill with appropriate values
        numeric_cols = ['latitude', 'longitude', 'depth', 'mag', 'nst', 'gap', 
                       'dmin', 'rms', 'horizontalError', 'depthError', 'magError', 'magNst']
        
        for col in numeric_cols:
            if col in self.df.columns:
                missing_count = self.df[col].isnull().sum()
                if missing_count > 0:
                    issues_found[col] = missing_count
                    # Fill with median for error columns, 0 for counters
                    if 'Error' in col or 'error' in col.lower():
                        self.df[col].fillna(self.df[col].median(), inplace=True)
                    elif col in ['gap', 'nst']:
                        self.df[col].fillna(0, inplace=True)
                    else:
                        self.df[col].fillna(self.df[col].median(), inplace=True)
                    print(f"✓ Filled {missing_count} missing values in '{col}'")
        
        # Text columns - fill with 'Unknown'
        text_cols = ['place', 'magType']
        for col in text_cols:
            if col in self.df.columns:
                missing_count = self.df[col].isnull().sum()
                if missing_count > 0:
                    issues_found[col] = missing_count
                    self.df[col].fillna('Unknown', inplace=True)
                    print(f"✓ Filled {missing_count} missing '{col}' with 'Unknown'")
        
        self.cleaning_report['missing_values'] = issues_found
    
    def remove_duplicates(self):
        """Remove duplicate records"""
        print("\n" + "="*80)
        print("REMOVING DUPLICATES")
        print("="*80)
        
        initial_count = len(self.df)
        
        # Remove completely identical rows
        self.df = self.df.drop_duplicates()
        full_dupes_removed = initial_count - len(self.df)
        if full_dupes_removed > 0:
            print(f"✓ Removed {full_dupes_removed} completely identical rows")
        
        # For ID duplicates, keep the most recently updated record
        if 'id' in self.df.columns and 'updated' in self.df.columns:
            self.df['updated'] = pd.to_datetime(self.df['updated'], errors='coerce')
            self.df = self.df.sort_values('updated', ascending=False)
            initial_count = len(self.df)
            self.df = self.df.drop_duplicates(subset=['id'], keep='first')
            id_dupes_removed = initial_count - len(self.df)
            if id_dupes_removed > 0:
                print(f"✓ Removed {id_dupes_removed} duplicate IDs (kept most recent)")
        
        self.cleaning_report['duplicates_removed'] = full_dupes_removed + id_dupes_removed
    
    def validate_and_standardize_formats(self):
        """Validate and standardize data formats"""
        print("\n" + "="*80)
        print("VALIDATING AND STANDARDIZING FORMATS")
        print("="*80)
        
        validation_issues = {}
        
        # Validate coordinates
        print("\n✓ Validating geographic coordinates...")
        lat_issues = ((self.df['latitude'] < -90) | (self.df['latitude'] > 90)).sum()
        lon_issues = ((self.df['longitude'] < -180) | (self.df['longitude'] > 180)).sum()
        
        if lat_issues > 0:
            validation_issues['invalid_latitude'] = lat_issues
            print(f"  ⚠ Found {lat_issues} invalid latitude values")
            self.df = self.df[(self.df['latitude'] >= -90) & (self.df['latitude'] <= 90)]
        
        if lon_issues > 0:
            validation_issues['invalid_longitude'] = lon_issues
            print(f"  ⚠ Found {lon_issues} invalid longitude values")
            self.df = self.df[(self.df['longitude'] >= -180) & (self.df['longitude'] <= 180)]
        
        # Validate magnitude
        print("✓ Validating magnitude values...")
        mag_issues = ((self.df['mag'] < -2) | (self.df['mag'] > 10)).sum()
        if mag_issues > 0:
            validation_issues['invalid_magnitude'] = mag_issues
            print(f"  ⚠ Found {mag_issues} unusual magnitude values (outside -2 to 10 range)")
        
        # Validate depth
        print("✓ Validating depth values...")
        depth_issues = (self.df['depth'] < 0).sum()
        if depth_issues > 0:
            validation_issues['negative_depth'] = depth_issues
            print(f"  ⚠ Found {depth_issues} negative depth values")
            self.df = self.df[self.df['depth'] >= 0]
        
        # Standardize date/time formats
        print("✓ Standardizing date/time formats...")
        self.df['time'] = pd.to_datetime(self.df['time'], errors='coerce')
        self.df['updated'] = pd.to_datetime(self.df['updated'], errors='coerce')
        time_issues = self.df['time'].isnull().sum()
        if time_issues > 0:
            validation_issues['invalid_time_format'] = time_issues
            print(f"  ⚠ Found {time_issues} unparseable timestamps")
            self.df = self.df[self.df['time'].notna()]
        
        # Round numeric columns for consistency
        print("✓ Standardizing numeric precision...")
        numeric_round_cols = {
            'latitude': 4,
            'longitude': 4,
            'depth': 2,
            'mag': 2,
            'horizontalError': 2,
            'depthError': 2,
            'magError': 3,
            'dmin': 3,
            'rms': 2,
            'gap': 0,
            'nst': 0
        }
        
        for col, decimals in numeric_round_cols.items():
            if col in self.df.columns:
                self.df[col] = self.df[col].round(decimals)
        
        self.cleaning_report['validation_issues'] = validation_issues
        print(f"✓ Format standardization complete")
    
    def check_data_integrity(self):
        """Verify data integrity constraints"""
        print("\n" + "="*80)
        print("DATA INTEGRITY CHECKS")
        print("="*80)
        
        integrity_issues = {}
        
        # Check for required fields
        print("\n✓ Checking required fields...")
        required_fields = ['time', 'latitude', 'longitude', 'depth', 'mag', 'id']
        for field in required_fields:
            if field in self.df.columns:
                missing = self.df[field].isnull().sum()
                if missing > 0:
                    integrity_issues[f'missing_{field}'] = missing
                    print(f"  ⚠ {missing} missing values in required field '{field}'")
        
        # Check for null IDs (should be unique identifiers)
        print("✓ Checking ID uniqueness...")
        unique_ids = len(self.df['id'].unique())
        duplicate_ids = len(self.df) - unique_ids
        if duplicate_ids > 0:
            integrity_issues['duplicate_ids'] = duplicate_ids
            print(f"  ⚠ Found {duplicate_ids} non-unique IDs")
        else:
            print(f"  ✓ All {unique_ids} IDs are unique")
        
        # Check magnitude type values
        print("✓ Checking magnitude type consistency...")
        if 'magType' in self.df.columns:
            valid_mag_types = self.df['magType'].value_counts()
            print(f"  Magnitude types found: {list(valid_mag_types.index)}")
        
        self.cleaning_report['integrity_checks'] = integrity_issues
    
    def generate_cleaning_summary(self):
        """Generate a detailed cleaning summary"""
        print("\n" + "="*80)
        print("CLEANING SUMMARY")
        print("="*80)
        
        print(f"\nOriginal Records: {len(self.original_df)}")
        print(f"Cleaned Records: {len(self.df)}")
        print(f"Records Removed: {len(self.original_df) - len(self.df)}")
        print(f"Data Retention: {(len(self.df) / len(self.original_df) * 100):.2f}%")
        
        print(f"\nCleaning Operations Performed:")
        print(f"  1. Handled missing values: {sum(self.cleaning_report.get('missing_values', {}).values())} fields fixed")
        print(f"  2. Removed duplicates: {self.cleaning_report.get('duplicates_removed', 0)} records")
        print(f"  3. Validation issues: {sum(self.cleaning_report.get('validation_issues', {}).values())} records removed")
        print(f"  4. Data integrity: {sum(self.cleaning_report.get('integrity_checks', {}).values())} issues found")
    
    def save_cleaned_data(self, output_file):
        """Save the cleaned data to a new CSV file"""
        self.df.to_csv(output_file, index=False)
        print(f"\n✓ Cleaned data saved to: {output_file}")
    
    def save_cleaning_report(self, report_file):
        """Save detailed cleaning report as JSON"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'original_records': len(self.original_df),
            'cleaned_records': len(self.df),
            'records_removed': len(self.original_df) - len(self.df),
            'data_retention_pct': round(len(self.df) / len(self.original_df) * 100, 2),
            'cleaning_details': self.cleaning_report,
            'columns': list(self.df.columns),
            'column_types': {col: str(dtype) for col, dtype in self.df.dtypes.items()}
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"✓ Cleaning report saved to: {report_file}")
    
    def run_full_cleaning(self):
        """Execute complete cleaning pipeline"""
        print("\n" + "█"*80)
        print("█" + " "*78 + "█")
        print("█" + " EARTHQUAKE DATA CLEANING & STRUCTURAL VALIDATION ".center(78) + "█")
        print("█" + " "*78 + "█")
        print("█"*80 + "\n")
        
        self.load_data()
        self.analyze_initial_issues()
        self.clean_missing_values()
        self.remove_duplicates()
        self.validate_and_standardize_formats()
        self.check_data_integrity()
        self.generate_cleaning_summary()
        
        return self.df


if __name__ == "__main__":
    # Configuration
    input_file = r"c:\Users\HP\Music\data_anal_inter\task1\earthquakes_2023_global.csv"
    output_file = r"c:\Users\HP\Music\data_anal_inter\task1\earthquakes_2023_cleaned.csv"
    report_file = r"c:\Users\HP\Music\data_anal_inter\task1\cleaning_report.json"
    
    # Run cleaning
    cleaner = EarthquakeDataCleaner(input_file)
    cleaned_df = cleaner.run_full_cleaning()
    
    # Save results
    cleaner.save_cleaned_data(output_file)
    cleaner.save_cleaning_report(report_file)
    
    print("\n" + "="*80)
    print("DATA CLEANING COMPLETE ✓")
    print("="*80)
