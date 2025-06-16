import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import os
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Compare two CSV files with interactive plots."
)
parser.add_argument("file1", type=str, help="Path to the first CSV file")
parser.add_argument("file2", type=str, help="Path to the second CSV file")
args = parser.parse_args()

# Load the CSV files
file1 = args.file1
file2 = args.file2

# Check if files exist
if not (os.path.exists(file1) and os.path.exists(file2)):
    raise FileNotFoundError("One or both CSV files not found")

df1 = pd.read_csv(file1, skiprows=[1])  # Skip the second row (units)
df2 = pd.read_csv(file2, skiprows=[1])  # Skip the second row (units)

# Ensure both DataFrames have the same columns and align them
common_columns = df1.columns.intersection(df2.columns)
df1 = df1[common_columns]
df2 = df2[common_columns]

# Select numerical columns for comparison
numerical_columns = df1.select_dtypes(include=[np.number]).columns.tolist()
if not numerical_columns:
    raise ValueError("No numerical columns found in the data")

segment1 = df1[numerical_columns]
segment2 = df2[numerical_columns]

# Initialize global variables
current_index = 0
fig = None
axes = None

def update_plot(index):
    """Update the plot for the given metric index."""
    global axes
    col = numerical_columns[index]

    # Clear previous plots
    for ax in axes:
        ax.clear()

    # Compute data
    data1 = segment1[col].values
    data2 = segment2[col].values
    
    # Handle NaN values: create a mask for non-NaN values in both arrays
    valid_mask = (~np.isnan(data1)) & (~np.isnan(data2))
    data1 = data1[valid_mask]
    data2 = data2[valid_mask]
    
    # Check if there's any valid data left
    if len(data1) == 0 or len(data2) == 0:
        axes[0].set_title(f"{col} Comparison - No valid data after NaN removal")
        axes[1].set_title(f"{col} Difference - No valid data after NaN removal")
        fig.suptitle(f"{col} (No valid data)")
        plt.draw()
        return

    # Compute difference
    diff = data2 - data1

    # Plot comparison
    axes[0].plot(data1, label=f"{col} ({os.path.splitext(file1)[0]})", alpha=0.7)
    axes[0].plot(data2, label=f"{col} ({os.path.splitext(file2)[0]})", alpha=0.7)
    axes[0].set_title(f"{col} Comparison")
    axes[0].set_xlabel("Sample Index")
    axes[0].set_ylabel(col)
    axes[0].legend()
    axes[0].grid(True)

    # Plot difference
    axes[1].plot(
        diff,
        label=f"{os.path.splitext(file2)[0]} - {os.path.splitext(file1)[0]}",
        color="purple",
    )
    axes[1].set_title(f"{col} Difference")
    axes[1].set_xlabel("Sample Index")
    axes[1].set_ylabel(f"Difference ({col})")
    axes[1].legend()
    axes[1].grid(True)

    # Update figure title with statistics
    mean_diff = diff.mean()
    std_diff = diff.std()
    max_diff = diff.max()
    min_diff = diff.min()
    fig.suptitle(
        f"{col} (Mean Diff: {mean_diff:.4f}, Std: {std_diff:.4f}, Max: {max_diff:.4f}, Min: {min_diff:.4f})"
    )

    plt.draw()

def save_comparison(event):
    """Save the comparison data for the current metric to a CSV file."""
    col = numerical_columns[current_index]
    data1 = segment1[col].values
    data2 = segment2[col].values
    valid_mask = (~np.isnan(data1)) & (~np.isnan(data2))
    data1 = data1[valid_mask]
    data2 = data2[valid_mask]
    
    if len(data1) == 0 or len(data2) == 0:
        print(f"No valid data to save for {col}")
        return

    diff = data2 - data1
    # Mark differences (non-zero differences as YES)
    diff_flag = np.where(np.abs(diff) > 0, "YES", "NO")
    
    # Create DataFrame for saving
    comparison_df = pd.DataFrame({
        "Index": np.arange(len(data1)),
        f"{col}_{os.path.splitext(file1)[0]}": data1,
        f"{col}_{os.path.splitext(file2)[0]}": data2,
        "Difference": diff,
        "Has_Difference": diff_flag
    })
    
    # Filter rows where Has_Difference is YES
    comparison_df = comparison_df[comparison_df["Has_Difference"] == "YES"]
    
    if comparison_df.empty:
        print(f"No differences found for {col}")
        return
    
    # Save to CSV
    output_filename = f"comparison_{col}.csv"
    comparison_df.to_csv(output_filename, index=False)
    print(f"Comparison saved to {output_filename}")

def next_plot(event):
    """Show the next metric's plots."""
    global current_index
    current_index = (current_index + 1) % len(numerical_columns)
    update_plot(current_index)

def prev_plot(event):
    """Show the previous metric's plots."""
    global current_index
    current_index = (current_index - 1) % len(numerical_columns)
    update_plot(current_index)

def quit_plot(event):
    """Close the plot window."""
    plt.close()

# Create the figure and subplots
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
fig.subplots_adjust(bottom=0.25, hspace=0.3)  # Increased space for buttons
axes = axes.flatten()

# Initialize the first plot
update_plot(current_index)

# Add centered buttons
ax_prev = plt.axes([0.30, 0.05, 0.1, 0.075])  # Adjusted position
ax_next = plt.axes([0.40, 0.05, 0.1, 0.075])  # Adjusted position
ax_save = plt.axes([0.50, 0.05, 0.1, 0.075])  # New save button
ax_quit = plt.axes([0.60, 0.05, 0.1, 0.075])  # Adjusted position
btn_prev = Button(ax_prev, "Previous")
btn_next = Button(ax_next, "Next")
btn_save = Button(ax_save, "Save Comp")
btn_quit = Button(ax_quit, "Quit")

# Connect button events
btn_prev.on_clicked(prev_plot)
btn_next.on_clicked(next_plot)
btn_save.on_clicked(save_comparison)
btn_quit.on_clicked(quit_plot)

# Show the plot
plt.show()