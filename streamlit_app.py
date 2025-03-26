# -*- coding: utf-8 -*-
"""streamlit_app.py

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1jMaVq9SNxHEDvsF1cjU3_Us2vxTwon-5
"""

# streamlit_app.py

import streamlit as st
import torch
import torch.nn.functional as F
import numpy as np
import random
from torch_geometric.nn import GCNConv

# Define a dictionary mapping drug indices to antibiotic names.
drug_names = {
    0: "Amoxicillin",
    1: "Ceftriaxone",
    2: "Ciprofloxacin",
    3: "Gentamicin",
    4: "Meropenem",
    5: "Imipenem",
    6: "Piperacillin/Tazobactam",
    7: "Colistin",
    8: "Aztreonam",
    9: "Levofloxacin",
    10: "Tigecycline",
    11: "Ceftazidime",
    12: "Ertapenem",
    13: "Ampicillin-Sulbactam",
    14: "Doripenem",
    15: "Cefepime",
    16: "Amikacin",
    17: "Trimethoprim-Sulfamethoxazole",
    18: "Ticarcillin-Clavulanate",
    19: "Nitrofurantoin"
}


# ---------------------------
# Define the same GNN Model as in training
# ---------------------------
class GCNEncoder(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels):
        super(GCNEncoder, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        return x

# Decoder function: compute dot product and apply sigmoid
def decode(embeddings, i, j):
    dot_product = (embeddings[i] * embeddings[j]).sum()
    return torch.sigmoid(dot_product)

# ---------------------------
# Re-generate the same dataset as in training (by setting the same seeds)
# ---------------------------
torch.manual_seed(42)
np.random.seed(42)
random.seed(42)

num_nodes = 20
feature_dim = 16
hidden_dim = 32

# Generate drug feature matrix x
x = torch.randn((num_nodes, feature_dim))

# Re-generate positive edges exactly as in training:
num_positive_edges = 30
positive_edges = set()
while len(positive_edges) < num_positive_edges:
    i = random.randint(0, num_nodes - 1)
    j = random.randint(0, num_nodes - 1)
    if i != j:
        edge = tuple(sorted((i, j)))
        positive_edges.add(edge)
positive_edges = list(positive_edges)
edge_index = torch.tensor(positive_edges, dtype=torch.long).t().contiguous()

# ---------------------------
# Load the trained model
# ---------------------------
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = GCNEncoder(feature_dim, hidden_dim).to(device)
model.load_state_dict(torch.load("gnn_model.pth", map_location=device))
model.eval()  # set model to evaluation mode

# Compute embeddings once using the full graph
x = x.to(device)
edge_index = edge_index.to(device)
with torch.no_grad():
    embeddings = model(x, edge_index)

# ---------------------------
# Build the Streamlit Web App
# ---------------------------
st.title("AI-Powered Antibiotic Synergy Predictor for Klebsiella pneumoniae")

st.write("""
This app uses a Graph Neural Network (GNN) to predict whether two antibiotics will work synergistically 
against **_Klebsiella pneumoniae_**, a high-priority drug-resistant superbug. 

Select two antibiotics to evaluate the likelihood of synergy based on learned patterns.
""")



# Input fields for drug indices
drug_i = st.number_input("Enter the index for Drug 1 (0-19):", min_value=0, max_value=num_nodes-1, value=0, step=1)
drug_j = st.number_input("Enter the index for Drug 2 (0-19):", min_value=0, max_value=num_nodes-1, value=1, step=1)

if st.button("Predict Synergy"):
    with torch.no_grad():
        # Calculate the predicted synergy probability using the decode function
        prob = decode(embeddings, drug_i, drug_j)
        # Determine label based on a threshold (0.5)
        label = "Synergistic ✅" if prob.item() > 0.5 else "Not Synergistic ❌"
        
        # Get the drug names from the dictionary
        drug_i_name = drug_names.get(drug_i, f"Drug {drug_i}")
        drug_j_name = drug_names.get(drug_j, f"Drug {drug_j}")
        
        # Display the result with drug names
        st.write(f"Predicted synergy probability between **{drug_i_name}** (Drug {drug_i}) and **{drug_j_name}** (Drug {drug_j}): **{prob.item():.4f}**")
        st.write(f"Prediction: **{label}**")
