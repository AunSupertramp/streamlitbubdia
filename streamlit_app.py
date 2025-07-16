import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(page_title="Interface Relationship Graph", layout="wide")
st.title("Project Interface Relationship Graph")

# --- Sidebar for File Upload and Instructions ---
with st.sidebar:
    st.header("Upload Your Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    st.markdown("---")
    st.header("CSV Format Guide")
    st.markdown("""
    Your CSV file must contain these exact column headers:
    - **`ID`**: Unique ID for the row (e.g., `#1`)
    - **`Interface`**: Main group (e.g., `ORLE`)
    - **`System`**: Specific system (e.g., `TRW`, `SE`)
    - **`Topics`**: High-level topic
    - **`Sub-Topics`**: Detailed description
    - **`Relationship`**: (Optional) ID of a related item (e.g., `#10`)
    """)

# --- Data Processing Function ---
def create_graph_data(df):
    """Processes the dataframe to create nodes and edges for the graph."""
    nodes = {}
    edges = []

    # Verify that required columns exist
    required_cols = ['ID', 'Interface', 'System', 'Sub-Topics', 'Relationship']
    if not all(col in df.columns for col in required_cols):
        st.error(f"CSV file is missing one or more required columns. Please ensure it contains: {', '.join(required_cols)}")
        return None, None

    # Process each row for hierarchical edges
    for _, row in df.iterrows():
        interface = row['Interface']
        system = row['System']
        # Use the ID to create a unique identifier for each sub-topic node
        sub_topic_id = f"{row['Sub-Topics']} ({row['ID']})"
        sub_topic_label = row['Sub-Topics']

        # Add Interface nodes
        if interface not in nodes:
            nodes[interface] = {'type': 'Interface', 'count': 0}
        nodes[interface]['count'] += 1
        
        # Add System nodes
        if system not in nodes:
            nodes[system] = {'type': 'System', 'count': 0}
        nodes[system]['count'] += 1

        # Add Sub-Topic nodes
        if sub_topic_id not in nodes:
            nodes[sub_topic_id] = {'type': 'Sub-Topic', 'label': sub_topic_label}

        # Add edges: Interface -> System -> Sub-Topic
        edges.append({'source': interface, 'target': system, 'kind': 'Hierarchy'})
        edges.append({'source': system, 'target': sub_topic_id, 'kind': 'Hierarchy'})

    # Create a map from ID to the unique sub-topic ID for relationship mapping
    id_to_subtopic_id_map = {row['ID']: f"{row['Sub-Topics']} ({row['ID']})" for _, row in df.iterrows()}

    # Process the 'Relationship' column for direct relational edges between the lowest-level nodes
    for _, row in df.dropna(subset=['Relationship']).iterrows():
        source_id = row['ID']
        target_id_str = str(row['Relationship'])
        
        if '#' not in target_id_str:
            target_id = f"#{''.join(filter(str.isdigit, target_id_str))}"
        else:
            target_id = target_id_str

        # Check if both source and target IDs exist in our map
        if source_id in id_to_subtopic_id_map and target_id in id_to_subtopic_id_map:
            # Get the unique sub-topic node IDs for the source and target
            source_sub_topic_node = id_to_subtopic_id_map[source_id]
            target_sub_topic_node = id_to_subtopic_id_map[target_id]
            
            # Add the edge between the sub-topic nodes
            edges.append({
                'source': source_sub_topic_node,
                'target': target_sub_topic_node,
                'kind': 'Relation',
                'title': f"Explicit Relation: {source_id} → {target_id}"
            })

    return nodes, edges

# --- Main Application Logic ---
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        nodes, edges = create_graph_data(df)

        if nodes and edges:
            net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white', notebook=True, directed=True)

            # Add nodes to the network
            for node_id, data in nodes.items():
                if data['type'] == 'Interface':
                    size = 25 + data.get('count', 0) * 1.5
                    color = '#00A0B0' # Blue
                    title = f"Type: Interface<br>Connection Count: {data.get('count', 0)}"
                    label = node_id
                elif data['type'] == 'System':
                    size = 15 + data.get('count', 0) * 1.5
                    color = '#EDC951' # Yellow
                    title = f"Type: System<br>Interface Count: {data.get('count', 0)}"
                    label = node_id
                else: # Sub-Topic
                    size = 10
                    color = '#CBE86B' # Green
                    title = f"Type: Sub-Topic<br>Name: {data.get('label', '')}"
                    label = data.get('label', '') # Use the shorter label for display

                net.add_node(node_id, label=label, title=title, size=size, color=color)

            # Add edges to the network
            for edge in edges:
                if edge['kind'] == 'Hierarchy':
                    net.add_edge(edge['source'], edge['target'], color='#CCCCCC', width=1)
                else: # Relation
                    net.add_edge(edge['source'], edge['target'], title=edge.get('title', ''), color='#FF4500', width=3, dashes=True)

            # Configure physics for a better layout that stabilizes
            net.set_options("""
            var options = {
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -80,
                  "centralGravity": 0.01,
                  "springLength": 150,
                  "springConstant": 0.08,
                  "avoidOverlap": 0.5
                },
                "solver": "forceAtlas2Based",
                "stabilization": {
                  "iterations": 1000
                }
              }
            }
            """)

            net.save_graph('interface_graph.html')
            with open('interface_graph.html', 'r', encoding='utf-8') as html_file:
                components.html(html_file.read(), height=820)

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("Please upload a CSV file using the sidebar to generate the graph.")
