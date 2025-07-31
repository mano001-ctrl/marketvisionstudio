import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import gc

def run():
    st.title("🧮 Expected P&L Simulator")

    # --- Sidebar Inputs ---
    win_prob = st.sidebar.slider("Win Probability", 0.0, 1.0, 0.80, 0.01)
    win_exp = st.sidebar.slider("Win Expectation", 0.0, 200.0, 90.0, 1.0)
    loss_exp = st.sidebar.slider("Loss Expectation", -200.0, 0.0, -200.0, 1.0)

    # --- Compute Expectation ---
    loss_prob = 1.0 - win_prob
    expected_pl = win_prob * win_exp + loss_prob * loss_exp
    st.markdown(f"**Expected P/L:** {expected_pl:.2f}")

    # --- Run Simulation on Button Click ---
    if st.button("Run Simulation"):
        try:
            steps = 100  # Smaller step size
            result = np.zeros(steps + 1)

            # Simulate
            result[1:] = np.where(
                np.random.rand(steps) < win_prob,
                win_exp,
                loss_exp
            )

            cumulative = np.cumsum(result)

            # Memory cap guard
            if len(cumulative) > 1000 or np.any(np.abs(cumulative) > 1e6):
                st.error("⚠️ Simulation exceeds memory or value bounds.")
                return

            # Smaller figure size
            fig, ax = plt.subplots(figsize=(5, 2.5))
            ax.plot(cumulative, label="Cumulative P/L", linewidth=2)
            ax.axhline(y=0, color="gray", linestyle="--", linewidth=1)
            ax.set_title("Simulated P/L")
            ax.set_xlabel("Day")
            ax.set_ylabel("Cumulative P/L")
            ax.legend()

            st.pyplot(fig)

            # Garbage collection
            gc.collect()

        except Exception as e:
            st.error(f"❌ Simulation failed: {e}")
