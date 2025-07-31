import streamlit as st
import matplotlib.pyplot as plt
import gc

def run():
    st.title("🧮 Expected P&L Simulator (Safe Mode)")

    # Sidebar controls
    win_prob = st.sidebar.slider("Win Probability", 0.0, 1.0, 0.80, 0.01)
    win_exp = st.sidebar.slider("Win Expectation", 0.0, 200.0, 90.0, 1.0)
    loss_exp = st.sidebar.slider("Loss Expectation", -200.0, 0.0, -200.0, 1.0)

    # Compute expectation
    loss_prob = 1.0 - win_prob
    expected_pl = win_prob * win_exp + loss_prob * loss_exp
    st.markdown(f"**Expected P/L:** {expected_pl:.2f}")

    # Button trigger
    if st.button("Run Simulation"):
        try:
            steps = 100  # Keep it light
            cumulative_pl = [0]
            running_sum = 0

            for _ in range(steps):
                trade = win_exp if st.session_state.get("rand_val", 0.5) < win_prob else loss_exp
                running_sum += trade
                cumulative_pl.append(running_sum)

                # Memory safety: cap value range
                if abs(running_sum) > 1_000_000:
                    st.error("⚠️ Simulation value overflow.")
                    return

            # Final memory cap
            if len(cumulative_pl) > 1000:
                st.error("⚠️ Simulation result too long.")
                return

            # Plot
            fig, ax = plt.subplots(figsize=(5, 2.5))
            ax.plot(cumulative_pl, label="Cumulative P/L", linewidth=2)
            ax.axhline(0, color="gray", linestyle="--", linewidth=1)
            ax.set_title("Simulated Trading Path")
            ax.set_xlabel("Step")
            ax.set_ylabel("P/L")
            ax.legend()
            st.pyplot(fig)

            # Force cleanup
            plt.close(fig)

        except Exception as e:
            st.error(f"❌ Simulation failed: {e}")
