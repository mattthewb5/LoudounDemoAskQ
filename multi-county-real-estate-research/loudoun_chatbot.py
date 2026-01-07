"""
Loudoun County Property Research Assistant Chatbot

A Streamlit-based chat interface using Claude API function calling
with 20 integrated property analysis tools.

Run with:
    streamlit run loudoun_chatbot.py
"""

import streamlit as st
import os
from core.claude_integration import ClaudeChatHandler
print(f"Loading .env from: {dotenv_path}")
# DEBUG: Print what keys are loaded
print("=" * 60)
print("DEBUG: Environment Variables Check")
print("=" * 60)
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
if anthropic_key:
    print(f"ANTHROPIC_API_KEY found: {anthropic_key[:20]}... (length: {len(anthropic_key)})")
else:
    print("ANTHROPIC_API_KEY: NOT FOUND")
    
google_key = os.getenv('GOOGLE_MAPS_API_KEY')
if google_key:
    print(f"GOOGLE_MAPS_API_KEY found: {google_key[:10]}... (length: {len(google_key)})")
else:
    print("GOOGLE_MAPS_API_KEY: NOT FOUND")
print("=" * 60)
import os
import sys
from pathlib import Path

# Ensure core module is importable
_APP_DIR = Path(__file__).parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Loudoun County Property Research Assistant",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import after page config
from core.claude_integration import ClaudeChatHandler, ANTHROPIC_AVAILABLE

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize session state for chat."""
    if "chat_state" not in st.session_state:
        st.session_state.chat_state = {
            "messages": [],              # Claude API format conversation history
            "display_messages": [],      # Messages for UI display
            "current_address": None,     # Last property address mentioned
            "current_coords": None,      # (lat, lon) tuple
            "formatted_address": None,   # Clean formatted address from geocoding
            "session_cost": 0.0,         # Running total
            "tools_called": [],          # All tools used this session
            "last_query_cost": 0.0,      # Cost of last query
            "last_tools_called": [],     # Tools called in last query
        }

    if "dev_mode" not in st.session_state:
        st.session_state.dev_mode = False


# =============================================================================
# CHAT HANDLER (CACHED)
# =============================================================================

@st.cache_resource
def get_chat_handler():
    """Get cached ClaudeChatHandler instance."""
    try:
        return ClaudeChatHandler()
    except Exception as e:
        return None


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar():
    """Render sidebar with developer options."""
    with st.sidebar:
        st.header("Options")

        # New Chat Button
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.chat_state = {
                "messages": [],
                "display_messages": [],
                "current_address": None,
                "current_coords": None,
                "formatted_address": None,
                "session_cost": 0.0,
                "tools_called": [],
                "last_query_cost": 0.0,
                "last_tools_called": [],
            }
            st.rerun()

        st.divider()

        # Developer Mode Toggle
        st.session_state.dev_mode = st.checkbox(
            "🔧 Developer Mode",
            value=st.session_state.dev_mode
        )

        if st.session_state.dev_mode:
            st.divider()
            st.subheader("Debug Info")

            # Current Property Context
            if st.session_state.chat_state["current_address"]:
                st.info(f"**Current Property:**\n{st.session_state.chat_state['formatted_address'] or st.session_state.chat_state['current_address']}")
                if st.session_state.chat_state["current_coords"]:
                    lat, lon = st.session_state.chat_state["current_coords"]
                    st.caption(f"Coords: ({lat:.6f}, {lon:.6f})")
            else:
                st.info("No property context set")

            st.divider()

            # Cost Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Last Query",
                    f"${st.session_state.chat_state['last_query_cost']:.4f}"
                )
            with col2:
                st.metric(
                    "Session Total",
                    f"${st.session_state.chat_state['session_cost']:.4f}"
                )

            # Last Tools Called
            if st.session_state.chat_state["last_tools_called"]:
                st.subheader("Last Tools Called")
                for tool in st.session_state.chat_state["last_tools_called"]:
                    st.code(tool)

            # All Session Tools
            if st.session_state.chat_state["tools_called"]:
                with st.expander("All Session Tools"):
                    st.json(st.session_state.chat_state["tools_called"])

            # Message Count
            st.caption(f"Messages in history: {len(st.session_state.chat_state['messages'])}")


# =============================================================================
# MAIN CHAT INTERFACE
# =============================================================================

def render_chat():
    """Render main chat interface."""
    # Header
    st.title("🏡 Loudoun County Property Research Assistant")
    st.markdown("Ask questions about any property in Loudoun County, Virginia")

    # API Key Check
    if not os.getenv('ANTHROPIC_API_KEY'):
        st.error("⚠️ ANTHROPIC_API_KEY not set. Please set environment variable.")
        st.code("export ANTHROPIC_API_KEY='your-api-key'")
        st.stop()

    if not ANTHROPIC_AVAILABLE:
        st.error("⚠️ anthropic package not installed. Please install with: pip install anthropic")
        st.stop()

    # Get handler
    handler = get_chat_handler()
    if handler is None:
        st.error("⚠️ Failed to initialize chat handler. Check API key and try again.")
        st.stop()

    # Example queries (only show if no messages yet)
    if not st.session_state.chat_state["display_messages"]:
        st.markdown("### Try asking:")

        example_queries = [
            "What schools serve 43422 Cloister Pl, Leesburg VA?",
            "Is 21627 Stableview Dr, Ashburn VA in a flood zone?",
            "What have homes sold for near 43422 Cloister Pl, Leesburg VA?",
            "Tell me about metro access for 44031 Pipeline Plaza, Ashburn VA",
            "What's the development activity near Brambleton?",
            "Give me a property analysis for 21627 Stableview Dr, Ashburn VA"
        ]

        cols = st.columns(2)
        for i, query in enumerate(example_queries):
            with cols[i % 2]:
                if st.button(f"📍 {query[:50]}...", key=f"example_{i}", use_container_width=True):
                    # Set this as the user input
                    st.session_state.pending_query = query
                    st.rerun()

    st.divider()

    # Chat container
    chat_container = st.container()

    # Display conversation history
    with chat_container:
        for msg in st.session_state.chat_state["display_messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Check for pending query from example buttons
    pending_query = st.session_state.get("pending_query", None)
    if pending_query:
        del st.session_state.pending_query
        process_user_input(pending_query, handler)

    # Chat input
    user_input = st.chat_input("Ask about a Loudoun County property...")

    if user_input:
        process_user_input(user_input, handler)


def process_user_input(user_input: str, handler: ClaudeChatHandler):
    """Process user input and get response from Claude."""
    # Add user message to display
    st.session_state.chat_state["display_messages"].append({
        "role": "user",
        "content": user_input
    })

    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get response from Claude
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                # Call Claude with conversation history
                result = handler.chat(
                    user_message=user_input,
                    conversation_history=st.session_state.chat_state["messages"]
                )

                # Update session state
                st.session_state.chat_state["messages"] = result["conversation_history"]
                st.session_state.chat_state["last_query_cost"] = result["total_cost"]
                st.session_state.chat_state["session_cost"] += result["total_cost"]
                st.session_state.chat_state["last_tools_called"] = result["tools_called"]
                st.session_state.chat_state["tools_called"].extend(result["tools_called"])

                # Update property context if geocoded
                if result.get("geocoded_address"):
                    geo = result["geocoded_address"]
                    st.session_state.chat_state["current_address"] = geo.get("address")
                    st.session_state.chat_state["formatted_address"] = geo.get("formatted_address")
                    st.session_state.chat_state["current_coords"] = (geo["lat"], geo["lon"])

                # Display response
                response_text = result["response_text"]
                st.markdown(response_text)

                # Add to display messages
                st.session_state.chat_state["display_messages"].append({
                    "role": "assistant",
                    "content": response_text
                })

                # Show tools called in dev mode (inline)
                if st.session_state.dev_mode and result["tools_called"]:
                    with st.expander("🔧 Tools Called", expanded=False):
                        st.json({
                            "tools": result["tools_called"],
                            "api_cost": f"${result.get('api_cost', 0):.4f}",
                            "tool_cost": f"${result.get('tool_cost', 0):.4f}",
                            "total_cost": f"${result['total_cost']:.4f}",
                            "execution_time": f"{result.get('execution_time', 0):.2f}s"
                        })

            except Exception as e:
                error_msg = str(e)
                st.error(f"I encountered an error: {error_msg}")

                # Provide helpful suggestions
                if "authentication" in error_msg.lower() or "401" in error_msg:
                    st.info("💡 Please check that your ANTHROPIC_API_KEY is valid.")
                elif "rate" in error_msg.lower() or "429" in error_msg:
                    st.info("💡 Rate limit reached. Please wait a moment and try again.")
                elif "geocod" in error_msg.lower():
                    st.info("💡 Could not find that address. Please check the address and try again.")
                else:
                    st.info("💡 Please try rephrasing your question or start a new conversation.")

                # Add error to display
                st.session_state.chat_state["display_messages"].append({
                    "role": "assistant",
                    "content": f"❌ Error: {error_msg}"
                })

    # Rerun to update sidebar metrics
    st.rerun()


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    init_session_state()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
