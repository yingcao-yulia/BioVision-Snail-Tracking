"""
Shapely Topological Buffer, Overlap Extraction & Quantitative Metrics Pipeline
--------------------------------------------------------------------------------
Calculates exact physical mucus trail overlaps across all dual-subject experiments.
Exports per-experiment pixel-level coordinates, generates true-scale overlap maps,
and computes master spatial-temporal analytics (Overlap Area %, Length %, Pixel Count).
"""

import os
import glob
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point
from shapely.prepared import prep

def run_overlap_analysis(csv_dir, pixel_out_dir, plot_out_dir, summary_csv, mucus_radius=20, padding=50):
    """
    Executes a two-pass batch analysis across all experiments to quantify 
    chemotaxis overlaps and produce visual maps and master summary CSVs.
    """
    os.makedirs(pixel_out_dir, exist_ok=True)
    os.makedirs(plot_out_dir, exist_ok=True)

    print("Pass 1: Scanning all files to find global axis limits for unified scaling...")
    global_min_x, global_max_x = float('inf'), float('-inf')
    global_min_y, global_max_y = float('inf'), float('-inf')

    all_csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    for file in all_csv_files:
        df = pd.read_csv(file)
        if not df.empty and 'X' in df.columns and 'Y' in df.columns:
            if df['X'].min() < global_min_x: global_min_x = df['X'].min()
            if df['X'].max() > global_max_x: global_max_x = df['X'].max()
            if df['Y'].min() < global_min_y: global_min_y = df['Y'].min()
            if df['Y'].max() > global_max_y: global_max_y = df['Y'].max()

    fixed_xlim = (global_min_x - padding, global_max_x + padding)
    fixed_ylim = (global_max_y + padding, global_min_y - padding)
    print(f"Global Scale locked! X: {fixed_xlim}, Y: {fixed_ylim}")

    print("Pass 2: Processing experiments, calculating overlapping pixels, and generating metrics...")
    summary_results = []

    for exp_id in range(1, 37):
        s1_file = os.path.join(csv_dir, f"{exp_id}-1_complete.csv")
        s2_file = os.path.join(csv_dir, f"{exp_id}-2_complete.csv")

        if not os.path.exists(s1_file) or not os.path.exists(s2_file):
            continue

        df1, df2 = pd.read_csv(s1_file), pd.read_csv(s2_file)

        # 1. Topological Line & Mucus Buffer Modeling
        s1_line = LineString(df1[['X', 'Y']].values)
        s2_line = LineString(df2[['X', 'Y']].values)

        s1_mucus_shape = s1_line.buffer(mucus_radius, cap_style=1, join_style=1)
        s2_mucus_shape = s2_line.buffer(mucus_radius, cap_style=1, join_style=1)

        overlapping_mucus_shape = s1_mucus_shape.intersection(s2_mucus_shape)

        # 2. Extract Overlapping Pixel Coordinates
        overlapping_pixels = []
        if not overlapping_mucus_shape.is_empty:
            minx, miny, maxx, maxy = overlapping_mucus_shape.bounds
            fast_overlap_shape = prep(overlapping_mucus_shape)

            for x in range(int(minx), int(maxx) + 1):
                for y in range(int(miny), int(maxy) + 1):
                    if fast_overlap_shape.contains(Point(x, y)):
                        overlapping_pixels.append({"X": x, "Y": y})

        # Save individual experiment pixel CSV
        pixel_csv_path = os.path.join(pixel_out_dir, f"experiment_{exp_id}_overlapping_pixels.csv")
        df_pixels = pd.DataFrame(overlapping_pixels)
        df_pixels.to_csv(pixel_csv_path, index=False)

        # 3. Calculate Quantitative Summary Metrics
        contact_distance = mucus_radius * 2
        contact_zone = s1_line.buffer(contact_distance, cap_style=1, join_style=1)
        overlapping_s2_path = s2_line.intersection(contact_zone)

        total_s2_length = s2_line.length
        overlap_length = overlapping_s2_path.length
        length_overlap_pct = (overlap_length / total_s2_length) * 100 if total_s2_length > 0 else 0

        total_s1_area = s1_mucus_shape.area
        total_s2_area = s2_mucus_shape.area
        overlap_area = overlapping_mucus_shape.area
        area_overlap_pct = (overlap_area / total_s2_area) * 100 if total_s2_area > 0 else 0

        summary_results.append({
            "Experiment_ID": exp_id,
            "Total_S1_Area_sq_px": round(total_s1_area, 2),
            "Total_S2_Area_sq_px": round(total_s2_area, 2),
            "Overlap_Area_sq_px": round(overlap_area, 2),
            "Total_S2_Length_px": round(total_s2_length, 2),
            "Overlap_Length_px": round(overlap_length, 2),
            "Length_Overlap_Pct": round(length_overlap_pct, 2),
            "Area_Overlap_Pct": round(area_overlap_pct, 2),
            "Overlap_Pixel_Count": len(overlapping_pixels)
        })

        # 4. Generate True-Scale Plot
        fig, ax = plt.subplots(figsize=(10, 8))

        x1, y1 = s1_mucus_shape.exterior.xy
        ax.fill(x1, y1, color='blue', alpha=0.2, label='S1 Mucus Trail')
        ax.plot(df1['X'], df1['Y'], color='blue', linewidth=2, label='S1 Center Path')

        x2, y2 = s2_mucus_shape.exterior.xy
        ax.fill(x2, y2, color='red', alpha=0.2, label='S2 Mucus Trail')
        ax.plot(df2['X'], df2['Y'], color='red', linewidth=2, linestyle='--', marker='o', markersize=4, label='S2 Center Path')

        if not df_pixels.empty:
            ax.scatter(df_pixels['X'], df_pixels['Y'], color='yellow', s=1, marker=',', alpha=0.05, zorder=3, label='Overlap Area')

        ax.scatter(df1['X'].iloc[0], df1['Y'].iloc[0], color='green', s=80, zorder=11, label='Start')
        ax.scatter(df1['X'].iloc[-1], df1['Y'].iloc[-1], color='purple', s=80, zorder=11, label='End')
        ax.scatter(df2['X'].iloc[0], df2['Y'].iloc[0], color='green', s=80, zorder=11)
        ax.scatter(df2['X'].iloc[-1], df2['Y'].iloc[-1], color='purple', s=80, zorder=11)

        ax.set_xlim(fixed_xlim)
        ax.set_ylim(fixed_ylim)
        ax.set_title(f"Experiment {exp_id}: True Scale Chemotaxis Overlap", fontsize=16)
        ax.set_xlabel("X Coordinate (Pixels)", fontsize=12)
        ax.set_ylabel("Y Coordinate (Pixels)", fontsize=12)
        ax.invert_yaxis()
        ax.legend(fontsize=10, loc='upper right')
        ax.grid(True, linestyle='--', alpha=0.5)

        plot_path = os.path.join(plot_out_dir, f"Experiment_{exp_id}_Overlap_Map.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Processed Experiment {exp_id} -> Saved plot & pixel CSV")

    # Save Master Summary
    summary_df = pd.DataFrame(summary_results)
    os.makedirs(os.path.dirname(summary_csv) if os.path.dirname(summary_csv) else '.', exist_ok=True)
    summary_df.to_csv(summary_csv, index=False)
    print(f"\nSuccess! Master summary saved to: {summary_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Batch Overlap & Quantitative Behavioral Analytics")
    parser.add_argument("--csv_dir", type=str, default="./outputs/interpolated_csvs", help="Directory with input CSVs")
    parser.add_argument("--pixel_dir", type=str, default="./outputs/experiment_overlapping_pixels", help="Directory for pixel CSVs")
    parser.add_argument("--plot_dir", type=str, default="./outputs/experiment_plots_with_overlap", help="Directory for plots")
    parser.add_argument("--summary_csv", type=str, default="./outputs/all_experiments_overlap_summary.csv", help="Master summary CSV path")
    args = parser.parse_args()

    run_overlap_analysis(args.csv_dir, args.pixel_dir, args.plot_dir, args.summary_csv)