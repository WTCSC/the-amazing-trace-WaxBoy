import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.ticker import MaxNLocator
import time
import os
import subprocess
import re

def execute_traceroute(destination):
    """
    Executes a traceroute to the specified destination and returns the output.

    Args:
        destination (str): The hostname or IP address to trace

    Returns:
        str: The raw output from the traceroute command
    """

    # Run traceroute with -I for each of the destinations
    process = subprocess.run(['traceroute', '-I', f"{destination}"], text=True, capture_output=True)
    
    output = process.stdout.split('\n')

    print(output)
    return output

            


def parse_traceroute(output):
    """
    Parses the raw traceroute output into a structured format.

    Args:
        traceroute_output (str): Raw output from the traceroute command

    Returns:
        list: A list of dictionaries, each containing information about a hop:
            - 'hop': The hop number (int)
            - 'ip': The IP address of the router (str or None if timeout)
            - 'hostname': The hostname of the router (str or None if same as ip)
            - 'rtt': List of round-trip times in ms (list of floats, None for timeouts)

    Example:
    ```
        [
            {
                'hop': 1,
                'ip': '172.21.160.1',
                'hostname': 'HELDMANBACK.mshome.net',
                'rtt': [0.334, 0.311, 0.302]
            },
            {
                'hop': 2,
                'ip': '10.103.29.254',
                'hostname': None,
                'rtt': [3.638, 3.630, 3.624]
            },
            {
                'hop': 3,
                'ip': None,  # For timeout/asterisk
                'hostname': None,
                'rtt': [None, None, None]
            }
        ]
    ```
    """

    ## Extract ip and hostname of requested destination
            
    request = output[0] # Details of traceroute request
    dest_ip = None
    dest_hostname = None # Initiate variables

    # Extract destination hostname by looking for 'traceroute to'
    match = re.search(r'traceroute to (\S+)', request)
    if match:
        dest_hostname = match.group(1)

    # Extract destination IP by looking for enclosed ip structure (8.8.8.8)
    match = re.search(r'\((\d{1,3}\.){3}\d{1,3}\)', request)
    if match:
        dest_ip = match.group()[1:-1] # Return without parenthesis

    # Set hostnome to none if the same as IP (redundant)
    if dest_hostname == dest_ip:
        dest_hostname = None 
        
    # Init data table output
    data = []

    for line in output[1:-1]:
        line = line.strip() # Strip
        
        # Init all segments
        hop = None
        ip = None
        hostname = None
        rtt = [None, None, None]


        # Find hop index
        match = re.search(r'^\d{1,2}', line)
        if match:
            hop = match.group()
        


        
        #Find round trip time (or '*'s)
        match = re.findall(r'\d\.\d{3} ms|\*', line)
        if match:
            if len(match) == 3:    
                for i in range(3):
                    entry = re.sub(r'[^0-9.*]', '', match[i])
                    if entry == '*':
                        rtt[i] = None
                    else:
                        rtt[i] = float(entry)

        match = re.search(r'\((\d{1,3}\.){3}\d{1,3}\)', line)
        if match:
            ip = match.group()
            ip = re.sub(r'[()]', '', ip)


        match = re.search(r'\S+ \((\d{1,3}\.){3}\d{1,3}\)', line)
        if match:
            hostname = match.group().split(' ')[0]   

        if hostname == ip:
            hostname = None
        

        # Init segments with hop index
        segments = {
            'hop': hop,
            'ip': ip,
            'hostname': hostname,
            'rtt': rtt
            }
        

        data.append(segments)
    print(data)
    return data

# ============================================================================ #
#                    DO NOT MODIFY THE CODE BELOW THIS LINE                    #
# ============================================================================ #
def visualize_traceroute(destination, num_traces=3, interval=5, output_dir='output'):
    """
    Runs multiple traceroutes to a destination and visualizes the results.

    Args:
        destination (str): The hostname or IP address to trace
        num_traces (int): Number of traces to run
        interval (int): Interval between traces in seconds
        output_dir (str): Directory to save the output plot

    Returns:
        tuple: (DataFrame with trace data, path to the saved plot)
    """
    all_hops = []

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print(f"Running {num_traces} traceroutes to {destination}...")

    for i in range(num_traces):
        if i > 0:
            print(f"Waiting {interval} seconds before next trace...")
            time.sleep(interval)

        print(f"Trace {i+1}/{num_traces}...")
        output = execute_traceroute(destination)
        hops = parse_traceroute(output)

        # Add timestamp and trace number
        timestamp = time.strftime("%H:%M:%S")
        for hop in hops:
            hop['trace_num'] = i + 1
            hop['timestamp'] = timestamp
            all_hops.append(hop)

    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(all_hops)

    # Calculate average RTT for each hop (excluding timeouts)
    df['avg_rtt'] = df['rtt'].apply(lambda x: np.mean([r for r in x if r is not None]) if any(r is not None for r in x) else None)

    # Plot the results
    plt.figure(figsize=(12, 6))

    # Create a subplot for RTT by hop
    ax1 = plt.subplot(1, 1, 1)

    # Group by trace number and hop number
    for trace_num in range(1, num_traces + 1):
        trace_data = df[df['trace_num'] == trace_num]

        # Plot each trace with a different color
        ax1.plot(trace_data['hop'], trace_data['avg_rtt'], 'o-',
                label=f'Trace {trace_num} ({trace_data.iloc[0]["timestamp"]})')

    # Add labels and legend
    ax1.set_xlabel('Hop Number')
    ax1.set_ylabel('Average Round Trip Time (ms)')
    ax1.set_title(f'Traceroute Analysis for {destination}')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend()

    # Make sure hop numbers are integers
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout()

    # Save the plot to a file instead of displaying it
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    safe_dest = destination.replace('.', '-')
    output_file = os.path.join(output_dir, f"trace_{safe_dest}_{timestamp}.png")
    plt.savefig(output_file)
    plt.close()

    print(f"Plot saved to: {output_file}")

    # Return the dataframe and the path to the saved plot
    return df, output_file

# Test the functions
if __name__ == "__main__":
    # Test destinations
    destinations = [
        "google.com",
        "amazon.com",
        "bbc.co.uk"  # International site
    ]
    for dest in destinations:
        df, plot_path = visualize_traceroute(dest, num_traces=3, interval=5)
        print(f"\nAverage RTT by hop for {dest}:")
        avg_by_hop = df.groupby('hop')['avg_rtt'].mean()
        print(avg_by_hop)
        print("\n" + "-"*50 + "\n")
