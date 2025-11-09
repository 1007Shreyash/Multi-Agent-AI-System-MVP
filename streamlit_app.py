# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import streamlit as st
import uuid
import tempfile
import os
import traceback
from agents.parent_agent import ParentAgent
from agents.whisper_agent import WhisperAgent
from database import Database
from st_audiorec import st_audiorec

st.set_page_config(
    page_title="Multi-Agent AI System", 
    page_icon="🤖", 
    layout="wide"
)

# --- Wrapper to catch all startup errors ---
try:
    # 1. Check for Firebase Credentials
    if "firebase_credentials" not in st.secrets:
        st.error("🔥 CRITICAL STARTUP ERROR: Firebase credentials not found.")
        st.info("Please add [firebase_credentials] section to .streamlit/secrets.toml")
        st.stop()

    # 2. Check for Gemini Key
    if "google_api_key" not in st.secrets:
        st.error("🔥 CRITICAL STARTUP ERROR: Google API Key not found.")
        st.info("Please add 'google_api_key' to .streamlit/secrets.toml")
        st.stop()

    # 3. Check for OpenAI Key (for Whisper)
    if "openai_api_key" not in st.secrets:
        st.error("🔥 CRITICAL STARTUP ERROR: OpenAI API Key not found.")
        st.info("Please add 'openai_api_key' to .streamlit/secrets.toml")
        st.stop()


    # --- Initialize Session State ---
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    # --- Initialize Database ---
    if 'db' not in st.session_state:
        try:
            # Convert the Streamlit Secrets object to a standard Python dict
            firebase_creds_dict = dict(st.secrets["firebase_credentials"])
            st.session_state.db = Database(firebase_creds_dict)
            st.session_state.db.init_tables()
        except Exception as e:
            st.error(f"Failed to initialize database. Is your secrets.toml file correct? Error: {e}")
            st.stop()

    # --- Get or Create User ---
    if 'user_id' not in st.session_state:
        st.session_state.user_id = st.session_state.db.get_or_create_user(st.session_state.session_id)
        if st.session_state.user_id is None:
            st.error("Failed to get or create a user. Check database connection and IAM permissions (needs 'Cloud Datastore User' role).")
            st.stop()

    # --- Initialize ParentAgent ---
    if 'parent_agent' not in st.session_state:
        st.session_state.parent_agent = ParentAgent(
            db=st.session_state.db, 
            user_id=st.session_state.user_id,
            google_api_key=st.secrets["google_api_key"]
        )

    # --- Main App UI ---
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 Agent Console", "📊 Analytics Dashboard", "📈 XP Progress", "🎭 PAEI Personality"])

    with tab1:
        st.title("🧠 Multi-Agent AI System MVP")
        st.write("A modular AI architecture with specialized agents coordinated by a Parent Agent.")

        # --- Sidebar ---
        st.sidebar.header("📊 System Status")
        try:
            # This now fetches the latest data on every rerun
            xp_stats = st.session_state.parent_agent.get_xp_stats()
            context = st.session_state.parent_agent.get_context()
            
            st.sidebar.metric("Level", xp_stats['level'])
            st.sidebar.metric("Total XP", xp_stats['total_xp'])
            st.sidebar.metric("Tasks Completed", xp_stats['tasks_completed'])
            
            progress_value = xp_stats['progress_percent'] / 100
            st.sidebar.progress(progress_value, text=f"Progress to Level {xp_stats['level'] + 1}")
            st.sidebar.caption(f"{xp_stats['xp_to_next_level']} XP to next level")
            
            st.sidebar.divider()
            st.sidebar.subheader("⚡ Current Context")
            st.sidebar.metric("Energy Level", f"{context['energy_level']}/100")
            st.sidebar.metric("Flow State", context['flow_state'].capitalize())
            st.sidebar.metric("Focus Score", f"{context['focus_score']}/100")
            
        except Exception as e:
            st.sidebar.error(f"Error loading stats: {str(e)}")


        st.sidebar.subheader("Dev Controls")
        if st.sidebar.button("⚠️ Reset My Data"):
            try:
                # 1. Clear the user from the database
                st.session_state.db.clear_user_data(st.session_state.user_id)
                
                # 2. Clear stale items from session state
                if 'user_id' in st.session_state:
                    del st.session_state.user_id
                if 'parent_agent' in st.session_state:
                    del st.session_state.parent_agent
                
                st.success("User data cleared! Rerunning to create a new session...")
                st.rerun()
                
            except Exception as e:
                st.sidebar.error(f"Error resetting: {e}")
        # --- End Sidebar ---

        st.divider()

        st.subheader("🎯 What can I help you with?")
        st.markdown("""
        Try commands like:
        - *"Send an email to the investor about our Q1 progress"*
        - *"Research the latest AI agent frameworks"*
        - *"Generate my performance report"*
        - *"What are the best practices for multi-agent systems?"*
        """)

        input_method = st.radio("Choose input method:", ["💬 Text", "🎤 Voice"], horizontal=True)
        
        user_input = ""
        
        if input_method == "💬 Text":
            user_input = st.text_input(
                "Type your command:", 
                placeholder="e.g., 'send email to team' or 'search quantum computing'",
                key="user_input_field"
            )
        
        else:
            # --- Voice Input ---
            st.info("🎤 Click the recorder to start/stop your voice command")
            
            # Check for placeholder key
            if "openai_api_key" not in st.secrets or not st.secrets["openai_api_key"]:
                 st.error("OpenAI API Key not found. Please add 'openai_api_key' to .streamlit/secrets.toml")
                 st.stop()
            elif st.secrets["openai_api_key"] == "sk-YOUR_OPENAI_KEY_GOES_HERE":
                 st.error("OpenAI API key is a placeholder. Please add your real key to .streamlit/secrets.toml to enable voice input.")
                 st.stop()

            audio_bytes = st_audiorec()
            
            if audio_bytes:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_audio_path = tmp_file.name
                
                try:
                    if 'whisper_agent' not in st.session_state:
                        st.session_state.whisper_agent = WhisperAgent(api_key=st.secrets["openai_api_key"])
                    
                    with st.spinner("🎧 Transcribing audio..."):
                        result = st.session_state.whisper_agent.transcribe_audio(tmp_audio_path)
                    
                    if result["status"] == "success":
                        user_input = result["transcription"]
                        st.success(f"Transcribed: {user_input}")
                    else:
                        st.error(result["message"])
                    
                    os.unlink(tmp_audio_path)
                except Exception as e:
                    st.error(f"Error processing audio: {str(e)}")
                    if os.path.exists(tmp_audio_path):
                        os.unlink(tmp_audio_path)
            # --- End Voice Input ---

        col1, col2 = st.columns([1, 1])

        with col1:
            run_button = st.button("🚀 Run Agent", type="primary", width = 'stretch')

        # Display the response after a rerun
        if 'last_response' in st.session_state:
            st.success("✅ Task completed!")
            st.markdown(st.session_state.last_response)
            del st.session_state.last_response # Clear it so it doesn't show again

        if run_button and user_input:
            with st.spinner("🤖 Agents working..."):
                try:
                    response = st.session_state.parent_agent.handle_request(user_input)
                    st.session_state.last_response = response # Save response for after the rerun
                    st.rerun() # Force a rerun to update the sidebar
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        # --- Chat History ---
        chat_history = st.session_state.db.get_chat_history(st.session_state.user_id, limit=10)
        
        if chat_history:
            st.divider()
            st.subheader("📜 Recent Conversation History")
            
            for i, entry in enumerate(reversed(chat_history[:5]), 1):
                if entry.get('timestamp'):
                    time_str = entry['timestamp'].strftime('%H:%M:%S')
                else:
                    time_str = "just now"
                    
                with st.expander(f"Task: {entry['input'][:60]}... ({time_str})"):
                    st.markdown(f"**Your Request:** {entry['input']}")
                    st.markdown(f"**Agent Used:** {entry['agent']}")
                    st.markdown("**Response:**")
                    st.markdown(entry['response'])

    with tab2:
        # --- Analytics Dashboard ---
        st.header("📊 Agent Performance Analytics")
        
        agent_metrics = st.session_state.db.get_agent_metrics(st.session_state.user_id)
        
        if agent_metrics:
            import plotly.graph_objects as go
            import plotly.express as px
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Agent Usage Distribution")
                agent_names = [m['agent'] for m in agent_metrics]
                call_counts = [m['calls'] for m in agent_metrics]
                
                fig_pie = px.pie(
                    values=call_counts,
                    names=agent_names,
                    title="Agent Calls by Type"
                )
                st.plotly_chart(fig_pie, width = 'stretch')
            
            with col2:
                st.subheader("XP Generation by Agent")
                xp_generated = [m['xp_generated'] for m in agent_metrics]
                
                fig_bar = go.Figure(data=[
                    go.Bar(x=agent_names, y=xp_generated, marker_color='lightblue')
                ])
                fig_bar.update_layout(
                    title="Total XP Generated per Agent",
                    xaxis_title="Agent Type",
                    yaxis_title="XP Generated"
                )
                st.plotly_chart(fig_bar, width = 'stretch')
            
            st.divider()
            st.subheader("📋 Detailed Agent Metrics")
            
            for metric in agent_metrics:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Agent", metric['agent'].upper())
                with col2:
                    st.metric("Total Calls", metric['calls'])
                with col3:
                    st.metric("XP Generated", metric['xp_generated'])
                with col4:
                    if metric['calls'] > 0:
                        avg_xp = round(metric['xp_generated'] / metric['calls'], 1)
                    else:
                        avg_xp = 0
                    st.metric("Avg XP/Call", avg_xp)
        else:
            st.info("No agent activity yet. Start using the system to see analytics!")

    with tab3:
        # --- XP Progress Tab ---
        st.header("📈 XP Progress & Task History")
        
        xp_stats = st.session_state.parent_agent.get_xp_stats()
        task_history = st.session_state.db.get_task_history(st.session_state.user_id, limit=50)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Level", xp_stats['level'], delta=None)
        with col2:
            st.metric("Total XP", xp_stats['total_xp'])
        with col3:
            st.metric("Tasks Completed", xp_stats['tasks_completed'])
        
        st.divider()
        
        if task_history:
            import plotly.express as px
            import pandas as pd
            
            st.subheader("XP Accumulation Over Time")
            
            cumulative_xp = []
            current_xp = 0
            task_numbers = []
            
            for task in reversed(task_history):
                current_xp += task['xp']
                cumulative_xp.append(current_xp)
                task_numbers.append(task['task_number'])
            
            df = pd.DataFrame({
                'Task Number': task_numbers,
                'Cumulative XP': cumulative_xp
            })
            
            fig_line = px.line(
                df, 
                x='Task Number', 
                y='Cumulative XP',
                title="XP Growth Curve",
                markers=True
            )
            st.plotly_chart(fig_line, width = 'stretch')
            
            st.divider()
            st.subheader("📋 Recent Task History")
            
            for i, task in enumerate(task_history[:10], 1):
                if task.get('created_at'):
                    time_str = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    time_str = "just now"
                    
                col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
                with col1:
                    st.write(f"**Task #{task['task_number']}**")
                with col2:
                    st.write(f"Type: {task['type']}")
                with col3:
                    st.write(f"+{task['xp']} XP")
                with col4:
                    st.write(f"{time_str}")
        else:
            st.info("No task history yet. Complete tasks to see your progress!")

    with tab4:
        # --- PAEI Personality Tab ---
        st.header("🎭 PAEI Personality Profile")
        
        st.markdown("""
        **PAEI Framework** analyzes your work patterns to identify your dominant productivity personality:
        - **Producer (P)**: Action-oriented, results-focused, execution-driven
        - **Administrator (A)**: Organized, systematic, process-oriented
        - **Entrepreneur (E)**: Creative, innovative, strategic thinker
        - **Integrator (I)**: Balanced, collaborative, holistic approach
        """)
        
        st.divider()
        
        try:
            profile = st.session_state.parent_agent.get_personality_profile()
            badge = st.session_state.parent_agent.get_personality_badge()
            recommendations = st.session_state.parent_agent.get_personality_recommendations()
            
            col1, col2 = st.columns([2, 3])
            
            with col1:
                st.subheader("Your Personality Badge")
                st.markdown(f"## {badge}")
                st.markdown(f"**Dominant Trait:** {profile['dominant_trait']}")
                st.markdown(f"**Strength:** {profile['dominant_score']:.1f}%")
                st.info(profile['profile_description'])
            
            with col2:
                st.subheader("PAEI Score Breakdown")
                
                import plotly.graph_objects as go
                
                traits = list(profile['scores'].keys())
                scores = list(profile['scores'].values())
                
                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=scores,
                    theta=traits,
                    fill='toself',
                    name='Your Profile'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 50]
                        )
                    ),
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig_radar, width = 'stretch')
            
            st.divider()
            
            st.subheader("💡 Adaptive Recommendations")
            st.markdown("Based on your personality profile, here are personalized tips:")
            
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"{i}. {rec}")
            
            st.divider()
            
            st.subheader("📊 Detailed PAEI Scores")
            
            for trait, score in profile['scores'].items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.progress(score / 100, text=f"{trait}: {score:.1f}%")
                with col2:
                    if trait == profile['dominant_trait_short']:
                        st.write("🌟 Dominant")
        
        except Exception as e:
            st.error(f"Error displaying personality profile: {e}")

    st.divider()
    st.caption("Developed for Persist Ventures Technical Challenge — Demonstrating modular AI architecture, persistent data storage, context awareness, PAEI adaptive behavior, and gamified task management. \n\n -By Shreyash Chougule \n [shreyash.v.chougule1903@gmail.com]")

except Exception as e:
    st.error(f"🚨 **FATAL APP ERROR** 🚨\n\nAn unexpected error occurred: **{e}**\n\n"
             "**Common Causes:**\n"
             "1. **Missing Libraries:** Have you run `pip install -r requirements.txt`?\n"
             "2. **API Keys:** Is your `.streamlit/secrets.toml` file correct?\n"
             "3. **Firebase Permissions:** Does your service account have the 'Cloud Datastore User' role?\n\n"
             "---")