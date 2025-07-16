import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components

# Set up the Streamlit page
st.set_page_config(page_title="Interface Relationship Graph", layout="wide")
st.title("Project Interface Relationship Graph")

# --- DATA PROCESSING ---
# This function processes the dataframe to create nodes and edges
def create_graph_data(df):
    nodes = {}
    edges = []

    # Process each row to define nodes and hierarchical edges
    for _, row in df.iterrows():
        interface = row['Interface']
        system = row['System']

        # Add nodes to the dictionary to ensure they are unique
        # Add interface node
        if interface not in nodes:
            nodes[interface] = {'type': 'Interface', 'count': 0}
        nodes[interface]['count'] += 1
        
        # Add system node
        if system not in nodes:
            nodes[system] = {'type': 'System', 'count': 0}
        nodes[system]['count'] += 1

        # Add hierarchical edge
        edges.append({
            'source': interface,
            'target': system,
            'kind': 'Hierarchy',
            'title': row['Sub-Topics']
        })

    # Process the 'Relationship' column for relational edges
    # Create a mapping from ID to System for easy lookup
    id_to_system_map = df.set_index('ID')['System'].to_dict()

    for _, row in df.dropna(subset=['Relationship']).iterrows():
        source_id = row['ID']
        target_id_str = row['Relationship']
        
        # Clean up the target ID (e.g., remove '#')
        target_id = f"#{''.join(filter(str.isdigit, target_id_str))}"

        if source_id in id_to_system_map and target_id in id_to_system_map:
            source_system = id_to_system_map[source_id]
            target_system = id_to_system_map[target_id]
            
            # Add relational edge
            edges.append({
                'source': source_system,
                'target': target_system,
                'kind': 'Relation',
                'title': f"Relation: {source_id} -> {target_id}"
            })

    return nodes, edges

# --- GRAPH VISUALIZATION ---
# Load data from the uploaded CSV
df = pd.read_csv('InterfaceData.csv')
nodes, edges = create_graph_data(df)

# Create a pyvis network object
net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white', notebook=True, directed=True)

# Add nodes to the network
for node_id, data in nodes.items():
    net.add_node(
        node_id,
        label=node_id,
        title=f"Type: {data['type']}<br>Interfaces: {data['count']}",
        size=15 + data['count'] * 2,  # Set size based on connection count
        color='#00A0B0' if data['type'] == 'Interface' else '#EDC951'
    )

# Add edges to the network
for edge in edges:
    net.add_edge(
        edge['source'],
        edge['target'],
        title=edge['title'],
        color='#CCCCCC' if edge['kind'] == 'Hierarchy' else '#FF4500' # Grey for hierarchy, OrangeRed for relations
    )

# Add physics options for a better layout
net.set_options("""
var options = {
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -50,
      "centralGravity": 0.01,
      "springLength": 230,
      "springConstant": 0.08,
      "avoidOverlap": 1
    },
    "maxVelocity": 50,
    "minVelocity": 0.1,
    "solver": "forceAtlas2Based",
    "stabilization": {
      "enabled": true,
      "iterations": 1000,
      "updateInterval": 50
    }
  }
}
""")

# Generate the HTML file and display it
try:
    path = '/tmp'
    net.save_graph(f'{path}/pyvis_graph.html')
    HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')
    components.html(HtmlFile.read(), height=820)
except Exception as e:
    st.error(f"An error occurred: {e}")