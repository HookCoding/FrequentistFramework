import re
import sys
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

def plot_minuit_continuous(filename, outname):
    # Regex to capture: [iteration] [FCN] [Edm] [NCalls]
    pattern = re.compile(r"VariableMetricBuilder\s+(\d+)\s+-\s+FCN\s+=\s+([-e\d.]+)\s+Edm\s+=\s+([-e\d.]+)\s+NCalls")

    cumulative_x = []
    edm_values = []
    star_indices = []
    
    total_counter = 0

    try:
        with open(filename, 'r') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    internal_iter = int(match.group(1))
                    edm = float(match.group(3))

                    # If the log's internal counter is 0, mark this global index for a star
                    if internal_iter == 0:
                        star_indices.append(total_counter)

                    cumulative_x.append(total_counter)
                    edm_values.append(edm)
                    total_counter += 1
                
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        sys.exit(1)

    if not cumulative_x:
        print("No matching data found.")
        return

    plt.figure(figsize=(12, 7))

    # 1. Plot the continuous line
    # We use a slight gradient or a solid color; 'viridis' over the whole length looks great
    plt.plot(cumulative_x, edm_values, color='#1f77b4', linewidth=1, alpha=1., label='Edm')

    for i, idx in enumerate(star_indices):
        label = "Run Reset" if i == 0 else None # Avoid cluttering legend
        plt.plot(cumulative_x[idx], edm_values[idx], marker='.', color='black', 
                 markersize=10, markeredgecolor='black', linestyle='None', zorder=5, label=label)

    # 3. Threshold line
    plt.axhline(y=1e-6, color='grey', linestyle='--', linewidth=1, label='Threshold ($10^{-6}$)')

    # Formatting
    plt.yscale('log')
#    plt.xscale('log')
    plt.xlabel('iteration')
    plt.ylabel('Estimated distance to minimum (Edm)')
#    plt.title(f'Continuous Minuit2 Trace: {len(star_indices)} Runs Identified')
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend()

    plt.savefig(outname, bbox_inches='tight')
    
    print("-" * 35)
    print(f"Total points plotted: {len(cumulative_x)}")
    print(f"Total runs (stars):   {len(star_indices)}")
    print(f"Plot saved to:        {outname}")
    print("-" * 35)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python plot_log.py <logfile> <outfile>")
    else:
        plot_minuit_continuous(sys.argv[1], sys.argv[2])
