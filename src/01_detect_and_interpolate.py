"""
Snail Detection and Trajectory Interpolation Pipeline
-----------------------------------------------------
Uses YOLOv8-World zero-shot detection to track biological targets across 
video frame sequences and performs linear interpolation to construct 
continuous temporal trajectories.
"""

import os
import argparse
import numpy as np
import pandas as pd
from ultralytics import YOLO

def process_snail_trajectories(base_dir, output_dir, model_path='yolov8s-world.pt', confidence=0.009):
    """
    Detects snails in subfolders of frame sequences and generates smoothed CSV trajectories.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Initialize YOLO Model with World Vocabulary
    model = YOLO(model_path)
    model.set_classes(["animal"])

    # Locate experiment subfolders
    subfolders = sorted([f.path for f in os.scandir(base_dir) if f.is_dir()])
    print(f"Found {len(subfolders)} experiment folders to process.")

    for folder_path in subfolders:
        folder_name = os.path.basename(folder_path)
        print(f"\n--- Processing folder: {folder_name} ---")

        # Track targets across frame sequence
        results = model.track(
            source=folder_path,
            conf=confidence,
            save=True,
            stream=True,
            project="./runs/detect",
            name=folder_name,
            exist_ok=True
        )

        trajectory_data = []

        # Extract Bounding Box Centroids
        for result in results:
            frame_name = os.path.basename(result.path)
            if len(result.boxes) > 0:
                x_center, y_center, width, height = result.boxes.xywh[0].cpu().numpy()
                trajectory_data.append({
                    "Frame": frame_name,
                    "X": int(x_center),
                    "Y": int(y_center)
                })

        if not trajectory_data:
            print(f"WARNING: No detections found in {folder_name}. Skipping interpolation.")
            continue

        # Data Cleaning and Missing Frame Interpolation
        df = pd.DataFrame(trajectory_data)
        df['Frame_Num'] = df['Frame'].str.extract(r'(\d+)').astype(int)

        full_frame_range = pd.DataFrame({
            'Frame_Num': np.arange(df['Frame_Num'].min(), df['Frame_Num'].max() + 1)
        })

        merged_df = pd.merge(full_frame_range, df, on='Frame_Num', how='left')
        merged_df['X'] = merged_df['X'].interpolate(method='linear').round()
        merged_df['Y'] = merged_df['Y'].interpolate(method='linear').round()

        # Save Interpolated Coordinates
        output_filename = os.path.join(output_dir, f"{folder_name}_complete.csv")
        merged_df.to_csv(output_filename, index=False)
        print(f"Success! Smoothed trajectory saved to {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YOLO Detection & Trajectory Interpolation")
    parser.add_argument("--base_dir", type=str, default="./data/frames", help="Directory containing frame subfolders")
    parser.add_argument("--output_dir", type=str, default="./outputs/interpolated_csvs", help="Output CSV directory")
    args = parser.parse_args()

    process_snail_trajectories(args.base_dir, args.output_dir)

