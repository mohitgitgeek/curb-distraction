import re
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.config import GEMINI_API_KEY
from src.rag.vector_store import VectorStore

class ProductivityCoach:
    """RAG-augmented productivity coach delivering dynamic, goal-tailored roadmaps with embedded resource links."""

    CURATED_RESOURCES = {
        "focus_timers": [
            {"title": "Pomofocus - Minimalist Pomodoro Timer", "url": "https://pomofocus.io/", "desc": "Customizable focus intervals with break alerts directly in your browser."},
            {"title": "Forest App - Gamified Phone & Desktop Focus", "url": "https://www.forestapp.cc/", "desc": "Grow virtual trees by staying off distracting websites."}
        ],
        "distraction_blockers": [
            {"title": "Unhook - Remove YouTube Recommended Videos & Shorts", "url": "https://unhook.app/", "desc": "Eliminates YouTube sidebar recommendations, comments, and shorts to stop mindless rabbit holes."},
            {"title": "Cold Turkey - Hardcore Distraction Blocker", "url": "https://getcoldturkey.com/", "desc": "Locks down distracting domains and apps with un-bypassable timers."},
            {"title": "Freedom - Multi-device App & Website Blocker", "url": "https://freedom.to/", "desc": "Syncs focus sessions across your phone, tablet, and PC."}
        ],
        "deep_work": [
            {"title": "Deep Work Framework (Cal Newport)", "url": "https://calnewport.com/deep-work-rules-for-focused-success-in-a-distracted-world/", "desc": "Core principles for high-output undistracted cognition."},
            {"title": "Huberman Lab: Dopamine & Focus Protocol", "url": "https://www.hubermanlab.com/episode/controlling-your-dopamine-for-motivation-focus-and-satisfaction", "desc": "Science-backed strategies to reset dopamine baselines and beat procrastination."}
        ],
        "academic_study": [
            {"title": "WolframAlpha Computational Intelligence", "url": "https://www.wolframalpha.com/", "desc": "Step-by-step problem solving for math, physics, science, and chemistry."},
            {"title": "Khan Academy Practice & Lessons", "url": "https://www.khanacademy.org/", "desc": "Structured explanations and interactive exercises across academic subjects."},
            {"title": "Quizlet Interactive Flashcards", "url": "https://quizlet.com/", "desc": "Active recall study tool for rapid memorization and exam prep."}
        ],
        "tech_coding": [
            {"title": "freeCodeCamp - Interactive Coding Challenges", "url": "https://www.freecodecamp.org/", "desc": "Replace passive tech video watching with hands-on coding practice."},
            {"title": "LeetCode Problem Sets", "url": "https://leetcode.com/problemset/", "desc": "Active algorithmic problem solving instead of tutorial bingeing."},
            {"title": "MDN Web Docs", "url": "https://developer.mozilla.org/", "desc": "Comprehensive technical documentation for web development."}
        ],
        "writing_research": [
            {"title": "Google Scholar Academic Search", "url": "https://scholar.google.com/", "desc": "Direct access to peer-reviewed research papers and literature."},
            {"title": "Hemingway Writing Clarity Editor", "url": "https://hemingwayapp.com/", "desc": "Highlights complex sentences and passive voice to streamline writing."}
        ]
    }

    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()
        self.api_key = GEMINI_API_KEY

    def generate_daily_plan(self, metrics: Dict[str, Any], user_goal: str = "Deep work and focused learning") -> Dict[str, Any]:
        """Synthesizes RAG-backed productivity roadmap specifically tailored to the user's declared goal and watch habits."""
        cleaned_goal = (user_goal or "Deep work and focused learning").strip()

        # Try Gemini API if key is available
        if self.api_key:
            try:
                ai_plan = self._generate_with_gemini(metrics, cleaned_goal)
                if ai_plan:
                    return ai_plan
            except Exception as e:
                print(f"[Coach] Gemini API call failed ({e}); falling back to dynamic goal engine.")

        # High-precision Dynamic Goal Decomposition Engine
        return self._generate_dynamic_rule_plan(metrics, cleaned_goal)

    def _generate_dynamic_rule_plan(self, metrics: Dict[str, Any], user_goal: str) -> Dict[str, Any]:
        total_time_fmt = metrics.get("total_watch_fmt", "0m")
        distraction_pct = metrics.get("distractive_pct", 0.0)
        peak_hour = metrics.get("peak_distraction_hour", "None")
        binge_count = metrics.get("binge_sessions_count", 0)
        total_shorts = metrics.get("total_shorts", 0)

        goal_lower = user_goal.lower()

        # Determine domain
        if any(w in goal_lower for w in ["homework", "study", "assignment", "exam", "quiz", "math", "physics", "class", "college", "school", "revision", "calculus"]):
            domain = "academic"
        elif any(w in goal_lower for w in ["code", "coding", "program", "python", "react", "bug", "software", "api", "backend", "frontend", "dbms", "database", "git", "project"]):
            domain = "coding"
        elif any(w in goal_lower for w in ["write", "writing", "essay", "paper", "article", "thesis", "report"]):
            domain = "writing"
        else:
            domain = "general"

        # Query vector store for related content
        distraction_matches = self.vector_store.similarity_search("shorts memes gaming entertainment comedy", top_k=3)
        sample_distraction = distraction_matches[0]["metadata"].get("title") if distraction_matches else "YouTube Shorts"

        suggestions = []

        # -------------------------------------------------------------
        # Step 1: Pre-Commitment & Digital Quarantine (Shorts Defense)
        # -------------------------------------------------------------
        if total_shorts > 0 or distraction_pct > 15:
            shorts_note = f"You watched {total_shorts} YouTube Shorts ({metrics.get('distractive_fmt', 'several minutes')}) today. Shorts flood the brain with rapid dopamine spikes, making tasks like '{user_goal}' feel agonizingly dull."
        else:
            shorts_note = f"Your baseline watch time is {total_time_fmt}. Starting '{user_goal}' requires eliminating subconscious tab-opening reflexes."

        suggestions.append({
            "id": "step_1_quarantine",
            "step_number": 1,
            "badge": "Phase 1: Digital Quarantine",
            "title": f"Quarantine YouTube & Stage Your Workspace for: '{user_goal}'",
            "diagnosis": shorts_note,
            "prescription": f"Close all YouTube tabs immediately. Set a hard rule: zero video streaming until Milestone 2 is complete. Place your materials for '{user_goal}' on full-screen.",
            "links": [
                {"label": "Install Unhook to block Shorts & recommendation sidebar", "url": self.CURATED_RESOURCES["distraction_blockers"][0]["url"]},
                {"label": "Lock distracting sites with Cold Turkey Blocker", "url": self.CURATED_RESOURCES["distraction_blockers"][1]["url"]}
            ]
        })

        # -------------------------------------------------------------
        # Step 2: Goal-Specific First Execution Sprint (45 Minutes)
        # -------------------------------------------------------------
        if domain == "academic":
            sprint_title = f"First 45-Min Solve Sprint: Tackle Hardest Homework Problems"
            sprint_diag = f"Procrastination on homework often stems from task ambiguity. When faced with difficult questions, the impulse is to open a 'quick short'."
            sprint_action = f"Divide '{user_goal}' into 3 clear chunks. Set a 45-minute countdown timer on Pomofocus. Attack the hardest question first while willpower is fresh. Write continuously without checking your phone."
            sprint_links = [
                {"label": "Start 45-min Pomofocus Timer", "url": self.CURATED_RESOURCES["focus_timers"][0]["url"]},
                {"label": "Step-by-step problem solver: WolframAlpha", "url": self.CURATED_RESOURCES["academic_study"][0]["url"]}
            ]
        elif domain == "coding":
            sprint_title = f"First 50-Min Deep Coding Block: Implementation over Tutorials"
            sprint_diag = f"Passive coding videos create an illusion of competence. Actual progress on '{user_goal}' only happens when writing code."
            sprint_action = f"Launch your IDE or terminal. Write the core function, schema, or test case for '{user_goal}' for 50 uninterrupted minutes without opening YouTube tutorials."
            sprint_links = [
                {"label": "Active Practice: freeCodeCamp", "url": self.CURATED_RESOURCES["tech_coding"][0]["url"]},
                {"label": "Start Pomofocus Timer", "url": self.CURATED_RESOURCES["focus_timers"][0]["url"]}
            ]
        elif domain == "writing":
            sprint_title = f"Drafting Sprint: Rapid Rough Draft for '{user_goal}'"
            sprint_diag = "Self-editing while drafting slows progress and triggers distraction browsing."
            sprint_action = f"Spend 45 minutes producing the raw text for '{user_goal}'. Don't stop to polish grammar or fix typos until the draft is finished."
            sprint_links = [
                {"label": "Hemingway Clarity Editor", "url": self.CURATED_RESOURCES["writing_research"][1]["url"]},
                {"label": "Google Scholar Reference Tool", "url": self.CURATED_RESOURCES["writing_research"][0]["url"]}
            ]
        else:
            sprint_title = f"Core Monotasking Sprint for '{user_goal}'"
            sprint_diag = f"Multitasking reduces cognitive IQ by up to 10 points. Focusing purely on '{user_goal}' requires single-task dedication."
            sprint_action = f"Run two back-to-back 25-minute Pomodoro sprints on '{user_goal}'. Keep a physical scratchpad next to your keyboard to jot down any distracting thoughts rather than opening browser tabs."
            sprint_links = [
                {"label": "Cal Newport's Deep Work Principles", "url": self.CURATED_RESOURCES["deep_work"][0]["url"]},
                {"label": "Launch Pomofocus Timer", "url": self.CURATED_RESOURCES["focus_timers"][0]["url"]}
            ]

        suggestions.append({
            "id": "step_2_sprint",
            "step_number": 2,
            "badge": "Phase 2: Deep Sprint",
            "title": sprint_title,
            "diagnosis": sprint_diag,
            "prescription": sprint_action,
            "links": sprint_links
        })

        # -------------------------------------------------------------
        # Step 3: The 'Stuck Protocol' & Curated Knowledge Backup
        # -------------------------------------------------------------
        if domain == "academic":
            stuck_title = f"Unsticking Protocol: What to Do When Homework Gets Hard"
            stuck_diag = f"When you hit an unsolved problem in '{user_goal}', the brain craves instant gratification (e.g. {sample_distraction}). That is the moment of maximum dropout."
            stuck_action = "If stuck for >5 minutes: Do NOT open YouTube. Instead, consult Khan Academy, check lecture notes, or use WolframAlpha to review the concept. If still stuck, mark it and move to problem 2."
            stuck_links = [
                {"label": "Review concepts on Khan Academy", "url": self.CURATED_RESOURCES["academic_study"][1]["url"]},
                {"label": "Active Recall on Quizlet", "url": self.CURATED_RESOURCES["academic_study"][2]["url"]}
            ]
        elif domain == "coding":
            stuck_title = f"Debugging Protocol: Avoid the Documentation Video Trap"
            stuck_diag = f"Searching YouTube for errors in '{user_goal}' leads straight into algorithm recommended feeds."
            stuck_action = "Read the official documentation (MDN or docs) and print debugging logs directly in code. Limit any documentation lookup to official written docs."
            stuck_links = [
                {"label": "Search Official Docs on MDN", "url": self.CURATED_RESOURCES["tech_coding"][2]["url"]},
                {"label": "LeetCode Algorithmic Practice", "url": self.CURATED_RESOURCES["tech_coding"][1]["url"]}
            ]
        else:
            stuck_title = f"Resistance Defense: Beat the Mid-Session Slump"
            stuck_diag = f"Between minutes 25 and 35 of working on '{user_goal}', boredom peaks. Autopilot browsing kicks in."
            stuck_action = "Stand up, stretch for 2 minutes, drink a full glass of water, and return immediately to your desk. Keep phone in another room."
            stuck_links = [
                {"label": "Huberman Dopamine & Motivation Reset", "url": self.CURATED_RESOURCES["deep_work"][1]["url"]},
                {"label": "Freedom Website Blocker", "url": self.CURATED_RESOURCES["distraction_blockers"][2]["url"]}
            ]

        suggestions.append({
            "id": "step_3_stuck",
            "step_number": 3,
            "badge": "Phase 3: Friction Shield",
            "title": stuck_title,
            "diagnosis": stuck_diag,
            "prescription": stuck_action,
            "links": stuck_links
        })

        # -------------------------------------------------------------
        # Step 4: Verification, Submission & Earned Leisure
        # -------------------------------------------------------------
        suggestions.append({
            "id": "step_4_finish",
            "step_number": 4,
            "badge": "Phase 4: Completion & Reward",
            "title": f"Review, Submit & Lock In Your Progress on '{user_goal}'",
            "diagnosis": "Finishing without explicit closure leaves open mental loops, increasing evening anxiety and late-night doomscrolling.",
            "prescription": f"Verify all parts of '{user_goal}'. Submit or file your work. Then reward yourself with an intentional, non-algorithmic reward (e.g. 15 minutes of music, exercise, or a walk).",
            "links": [
                {"label": "Gamify daily consistency with Forest App", "url": self.CURATED_RESOURCES["focus_timers"][1]["url"]},
                {"label": "Cal Newport's Shutdown Ritual Framework", "url": self.CURATED_RESOURCES["deep_work"][0]["url"]}
            ]
        })

        now_str = datetime.now().strftime("%I:%M %p")
        return {
            "summary": f"Generated at {now_str} for goal: '{user_goal}'. Based on your watch baseline ({total_time_fmt}, {total_shorts} Shorts), follow this 4-step execution roadmap:",
            "user_goal": user_goal,
            "domain": domain,
            "distraction_pct": distraction_pct,
            "total_watch_time": total_time_fmt,
            "total_shorts": total_shorts,
            "generated_at": now_str,
            "suggestions": suggestions
        }

    def _generate_with_gemini(self, metrics: Dict[str, Any], user_goal: str) -> Optional[Dict[str, Any]]:
        """Optional AI synthesis using Gemini when GEMINI_API_KEY is configured."""
        prompt = f"""
You are a high-performance productivity coach. The user wants to accomplish this specific goal today: "{user_goal}".
User's YouTube activity today:
- Total watch time: {metrics.get('total_watch_fmt')}
- Distraction ratio: {metrics.get('distractive_pct')}%
- Total YouTube Shorts: {metrics.get('total_shorts', 0)}
- Peak distraction hour: {metrics.get('peak_distraction_hour')}

Generate a concrete 4-step execution roadmap tailored specifically to "{user_goal}".
Return JSON format with a list of 4 objects under 'suggestions', each having:
- step_number: int
- badge: string
- title: string
- diagnosis: string (analyzing why YouTube distractions threaten this specific goal)
- prescription: string (actionable instructions for "{user_goal}")
- links: list of objects with 'label' and 'url'
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content)
            now_str = datetime.now().strftime("%I:%M %p")
            return {
                "summary": f"AI Plan generated at {now_str} for '{user_goal}'.",
                "user_goal": user_goal,
                "distraction_pct": metrics.get("distractive_pct", 0),
                "total_watch_time": metrics.get("total_watch_fmt", "0m"),
                "total_shorts": metrics.get("total_shorts", 0),
                "generated_at": now_str,
                "suggestions": parsed.get("suggestions", [])
            }
        return None
