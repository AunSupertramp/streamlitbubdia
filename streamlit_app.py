import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(page_title="Interface Relationship Graph", layout="wide")
st.title("Project Interface Relationship Graph")

# --- Data Processing Function ---
def create_graph_data(df):
    """Processes the dataframe to create nodes and edges for the graph."""
    nodes = {}
    edges = []
    
    # Identify standard columns and potential grouping columns
    standard_cols = ['ID', 'Interface', 'System', 'Topics', 'Sub-Topics', 'Relationship', 'Remark']
    grouping_cols = [col for col in df.columns if col not in standard_cols]

    # Process each row for hierarchical edges
    for _, row in df.iterrows():
        interface = row['Interface']
        system = row['System']
        sub_topic_id = f"{row['Sub-Topics']} ({row['ID']})"
        sub_topic_label = row['Sub-Topics']

        # Add Interface, System, and Sub-Topic nodes
        if interface not in nodes: nodes[interface] = {'type': 'Interface', 'count': 0}
        nodes[interface]['count'] += 1
        if system not in nodes: nodes[system] = {'type': 'System', 'count': 0}
        nodes[system]['count'] += 1
        if sub_topic_id not in nodes: nodes[sub_topic_id] = {'type': 'Sub-Topic', 'label': sub_topic_label}

        # Add hierarchical edges
        edges.append({'source': interface, 'target': system, 'kind': 'Hierarchy'})
        edges.append({'source': system, 'target': sub_topic_id, 'kind': 'Hierarchy'})

    # Create a map from ID to the unique sub-topic ID
    id_to_subtopic_id_map = {row['ID']: f"{row['Sub-Topics']} ({row['ID']})" for _, row in df.iterrows()}

    # Process the 'Relationship' column for direct relational edges
    for _, row in df.dropna(subset=['Relationship']).iterrows():
        source_id, target_id_str = row['ID'], str(row['Relationship'])
        target_id = f"#{''.join(filter(str.isdigit, target_id_str))}" if '#' not in target_id_str else target_id_str
        if source_id in id_to_subtopic_id_map and target_id in id_to_subtopic_id_map:
            source_node = id_to_subtopic_id_map[source_id]
            target_node = id_to_subtopic_id_map[target_id]
            edges.append({'source': source_node, 'target': target_node, 'kind': 'Relation', 'title': f"Relation: {source_id}→{target_id}"})

    return nodes, edges, grouping_cols

# --- Main Application Logic ---
# --- Sidebar ---
with st.sidebar:
    st.header("Upload Your Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    st.markdown("---")
    
    # Placeholder for group selector
    group_selector_placeholder = st.empty()

    st.header("CSV Format Guide")
    st.markdown("""
    - **Required Columns**: `ID`, `Interface`, `System`, `Topics`, `Sub-Topics`, `Relationship`
    - **Optional Grouping Columns**: Add columns with `TRUE` values to create visual groups.
    """)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        nodes, edges, grouping_cols = create_graph_data(df)
        
        # Add the group selector to the sidebar now that we have the column names
        selected_groups = group_selector_placeholder.multiselect("Select Groups to Display", options=grouping_cols)

        # Add group nodes and edges based on selection
        for group in selected_groups:
            if group in df.columns:
                # Add a central node for the group
                nodes[group] = {'type': 'Group'}
                # Connect all relevant sub-topic nodes to this group node
                for _, row in df[df[group] == True].iterrows():
                    sub_topic_id = f"{row['Sub-Topics']} ({row['ID']})"
                    if sub_topic_id in nodes:
                        edges.append({'source': group, 'target': sub_topic_id, 'kind': 'Group'})

        if nodes and edges:
            net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white', notebook=True, directed=False)

            # Add all nodes to the network
            for node_id, data in nodes.items():
                node_type = data.get('type')
                if node_type == 'Interface':
                    net.add_node(node_id, label=node_id, size=25, color='#00A0B0', title=f"Interface: {node_id}")
                elif node_type == 'System':
                    net.add_node(node_id, label=node_id, size=15, color='#EDC951', title=f"System: {node_id}")
                elif node_type == 'Sub-Topic':
                    net.add_node(node_id, label=data.get('label', ''), size=8, color='#CBE86B', title=f"Sub-Topic: {data.get('label', '')}")
                elif node_type == 'Group':
                    # This node is a hub for the group
                    net.add_node(
                        node_id, 
                        label=node_id, 
                        size=20,
                        shape='star', 
                        color='#FF69B4', # Hot Pink
                        title=f"Group: {node_id}"
                    )

            # Add all edges to the network
            for edge in edges:
                if edge['kind'] == 'Hierarchy':
                    net.add_edge(edge['source'], edge['target'], color='rgba(204, 204, 204, 0.3)', width=1)
                elif edge['kind'] == 'Relation':
                    net.add_edge(edge['source'], edge['target'], title=edge.get('title', ''), color='#FF4500', width=2.5, dashes=True)
                elif edge['kind'] == 'Group':
                    # These edges are now visible and styled to show the grouping
                    net.add_edge(edge['source'], edge['target'], color='rgba(255, 105, 180, 0.5)', width=1.5, dashes=True)
            
            # Configure physics
            net.set_options("""
            var options = {
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -100,
                  "centralGravity": 0.01,
                  "springLength": 100,
                  "springConstant": 0.08,
                  "avoidOverlap": 0.5
                },
                "solver": "forceAtlas2Based",
                "stabilization": { "iterations": 1000 }
              }
            }
            """)

            # Generate and display graph
            net.save_graph('interface_graph.html')
            with open('interface_graph.html', 'r', encoding='utf-8') as html_file:
                components.html(html_file.read(), height=820)

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV file to generate the graph.")

