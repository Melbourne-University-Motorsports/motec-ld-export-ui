import os
import sys
import pandas as pd
from typing import List, Tuple, Optional
import shutil

# Ensure motec-to-csv submodule is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../motec-to-csv/src'))

try:
    from motec_converter import parse_race_data, to_pandas, RaceData
except ImportError:
    raise ImportError("Could not import 'motec_converter'. Ensure submodule is initialized.")

class MotecProcessor:
    def __init__(self):
        pass

    def load_data(self, filepath: str) -> RaceData:
        """Loads the .ld file using the library."""
        try:
            return parse_race_data(filepath)
        except Exception as e:
            raise ValueError(f"Failed to parse file: {e}")

    def to_dataframes(self, race_data: RaceData) -> List[pd.DataFrame]:
        """Converts RaceData to a list of DataFrames (auto-split by library)."""
        return to_pandas(race_data)

    def scan_file(self, filepath: str) -> dict:
        """
        Parses the file and returns metadata about splits for preview.
        Returns: { 'filename': str, 'comment': str, 'runs': [{'duration': float, 'samples': int}, ...] }
        """
        race_data = self.load_data(filepath)
        dfs = self.to_dataframes(race_data)
        
        runs = []
        for df in dfs:
            if not df.empty:
                duration = df.index[-1] - df.index[0]
                runs.append({
                    'duration': duration,
                    'start': df.index[0],
                    'end': df.index[-1],
                    'samples': len(df)
                })
                
        return {
            'filepath': filepath,
            'comment': race_data.comment,
            'runs': runs
        }

    def process_file(
        self, 
        filepath: str, 
        output_dir: str, 
        enable_splitting: bool = True
    ) -> List[str]:
        """
        Full processing pipeline for a single file.
        Returns list of generated file paths.
        """
        race_data = self.load_data(filepath)
        
        # Extract comment for naming
        comment = race_data.comment if race_data.comment else "No_Comment"
        if not comment or comment == "No_Comment":
             if race_data.racetype: comment = race_data.racetype
             elif race_data.vehicle: comment = race_data.vehicle
        
        dfs = self.to_dataframes(race_data)
        
        # Note: If enable_splitting is strictly False, we might want to merge or just take first? 
        # For now we just use what library gives us (which is split). 
        # If user wants ONE file, we effectively export all splits anyway or we'd need to concat.
        # Given "auto-split" checkbox intent, if unchecked, maybe we should just Concatenate?
        # But indices would have gaps. 
        # Let's assume for now we just process valid chunks.

        created_files = []
        valid_dfs = [df for df in dfs if not df.empty]
        
        for i, df in enumerate(valid_dfs):
            # Name
            out_path = self.generate_filename(output_dir, comment, i, len(valid_dfs))
            
            # Export
            df.to_csv(out_path, float_format="%.3f")
            created_files.append(out_path)
            
        return created_files

    def generate_filename(self, output_dir: str, base_name: str, run_index: int, total_runs: int) -> str:
        """
        Generates a safe, unique filename.
        Format: {base_name}.csv or {base_name}_Run{i}.csv
        """
        # Sanitize base_name
        import re
        safe_name = re.sub(r'[<>:"/\\|?*]', '', base_name)
        safe_name = safe_name.strip()
        if not safe_name:
            safe_name = "Export"

        # Construct candidate name
        if total_runs > 1:
            candidate = f"{safe_name}_Run{run_index + 1}.csv"
        else:
            candidate = f"{safe_name}.csv"
            
        full_path = os.path.join(output_dir, candidate)
        
        # Handle collision
        counter = 1
        name_root, ext = os.path.splitext(candidate)
        while os.path.exists(full_path):
            new_candidate = f"{name_root}_{counter}{ext}"
            full_path = os.path.join(output_dir, new_candidate)
            counter += 1
            
        return full_path
