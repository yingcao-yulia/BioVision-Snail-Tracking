"""
Global-Scale Trajectory Visualization
--------------------------------------
Computes uniform bounding box scales across all experiments and generates
dual-layered chemotaxis movement plots with mucus trail simulations.
"""

import os
import glob
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def plot_chemotaxis_experiments(csv_dir, plot_output_dir, mucus_radius=20, padding=50):
    """
    Scans all CSVs for global scale locking, then generates normalized plots for experiments.
    """
    os.makedirs(plot_output_dir, exist_ok=True)

    print("Pass 1: Scanning all CSV files to lock global axis boundaries...")
    global_min_x, global_max_x = float('inf'), float('-inf')
    global_min_y, global_max_y = float('inf'), float('-inf')

    all_csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    for file in all_csv_files:
        df = pd.read_csv(file)
        if df['X'].min() < global_min_x: global_min_x = df['X'].min()
        if df['X'].max() > global_max_x: global_max_x = df['X'].max()
        if df['Y'].min() < global_min_y: global_min_y = df['Y'].min()
        if df['Y'].max() > global_max_y: global_max_y = df['Y'].max()

    fixed_xlim = (global_min_x - padding, global_max_x + padding)
    fixed_ylim = (global_max_y + padding, global_min_y - padding)
    print(f"Global Scale Locked! X: {fixed_xlim}, Y: {fixed_ylim}")

    print("Pass 2: Generating scaled comparison plots...")
    for exp_id in range(1, 37):
        s1_file = os.path.join(csv_dir, f"{exp_id}-1_complete.csv")
        s2_file = os.path.join(csv_dir, f"{exp_id}-2_complete.csv")

        if not os.path.exists(s1_file) or not os.path.exists(s2_file):
            continue

        df1, df2 = pd.read_csv(s1_file), pd.read_csv(s2_file)
        fig, ax = plt.subplots(figsize=(10, 8))

        # Render Snail 1 (Blue) & Snail 2 (Red)
        ax.plot(df1['X'], df1['Y'], color='blue', linewidth=mucus_radius, alpha=0.2, label='S1 Mucus Trail')
        ax.plot(df1['X'], df1['Y'], color='blue', linewidth=2, label='S1 Center Path')

        ax.plot(df2['X'], df2['Y'], color='red', linewidth=mucus_radius, alpha=0.2, label='S2 Mucus Trail')
        ax.plot(df2['X'], df2['Y'], color='red', linewidth=2, linestyle='--', marker='o', markersize=4, label='S2 Center Path')

        # Start & End Node Annotations
        ax.scatter(df1['X'].iloc[0], df1['Y'].iloc[0], color='green', s=80, zorder=5, label='Start')
        ax.scatter(df1['X'].iloc[-1], df1['Y'].iloc[-1], color='purple', s=80, zorder=5, label='End')
        ax.scatter(df2['X'].iloc[0], df2['Y'].iloc[0], color='green', s=80, zorder=5)
        ax.scatter(df2['X'].iloc[-1], df2['Y'].iloc[-1], color='purple', s=80, zorder=5)

        ax.set_xlim(fixed_xlim)
        ax.set_ylim(fixed_ylim)
        ax.set_title(f"Experiment {exp_id}: Chemotaxis Tracking", fontsize=16)
        ax.set_xlabel("X Coordinate (Pixels)", fontsize=12)
        ax.set_ylabel("Y Coordinate (Pixels)", fontsize=12)
        ax.legend(fontsize=10, loc='upper right')
        ax.grid(True, linestyle='--', alpha=0.5)

        output_filename = os.path.join(plot_output_dir, f"Experiment_{exp_id}_Plot.png")
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        plt.close(fig)

    print("Scaled plots successfully generated!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Normalized Trajectories")
    parser.add_argument("--csv_dir", type=str, default="./outputs/interpolated_csvs")
    parser.add_argument("--output_dir", type=str, default="./outputs/experiment_plots")
    args = parser.parse_args()

    plot_chemotaxis_experiments(args.csv_dir, args.output_dir)