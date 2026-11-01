from typing import List, Dict, Any, Optional
from src.rag.vector_store import VectorStore

class ProductivityCoach:
    """RAG-augmented productivity coach delivering actionable advice with embedded resource links."""

    CURATED_RESOURCES = {
        "focus_timers": [
            {"title": "Pomofocus - Minimalist Pomodoro Timer", "url": "https://pomofocus.io/", "desc": "Customizable focus intervals with break alerts directly in your browser."},
            {"title": "Forest App - Gamified Phone & Desktop Focus", "url": "https://www.forestapp.cc/", "desc": "Grow virtual trees by staying off distracting websites."}
        ],
        "distraction_blockers": [
            {"title": "Unhook - Remove YouTube Recommended Videos", "url": "https://unhook.app/", "desc": "Eliminates YouTube sidebar recommendations, comments, and shorts to stop mindless rabbit holes."},
            {"title": "Cold Turkey - Hardcore Distraction Blocker", "url": "https://getcoldturkey.com/", "desc": "Locks down distracting domains and apps with un-bypassable timers."},
            {"title": "Freedom - Multi-device App & Website Blocker", "url": "https://freedom.to/", "desc": "Syncs focus sessions across your phone, tablet, and PC."}
        ],
        "deep_work": [
            {"title": "Deep Work Framework (Cal Newport)", "url": "https://calnewport.com/deep-work-rules-for-focused-success-in-a-distracted-world/", "desc": "Core principles for high-output undistracted cognition."},
            {"title": "Huberman Lab: Dopamine & Focus Protocol", "url": "https://www.hubermanlab.com/episode/controlling-your-dopamine-for-motivation-focus-and-satisfaction", "desc": "Science-backed strategies to reset dopamine baselines and beat procrastination."}
        ],
        "active_learning": [
            {"title": "freeCodeCamp - Interactive Coding Challenges", "url": "https://www.freecodecamp.org/", "desc": "Replace passive tech video watching with hands-on coding practice."},
            {"title": "MIT OpenCourseWare", "url": "https://ocw.mit.edu/", "desc": "Structured, world-class university curricula and problem sets."},
            {"title": "LeetCode Problem Sets", "url": "https://leetcode.com/problemset/", "desc": "Active algorithmic problem solving instead of tutorial bingeing."}
        ]
    }

    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()

    def generate_daily_plan(self, metrics: Dict[str, Any], user_goal: str = "Maximum focus and deep work") -> Dict[str, Any]:
        """Synthesizes RAG-backed productivity recommendations tailored to user metrics and distraction patterns."""
        total_time_fmt = metrics.get("total_watch_fmt", "0m")
        distraction_pct = metrics.get("distractive_pct", 0.0)
        peak_hour = metrics.get("peak_distraction_hour", "None")
        binge_count = metrics.get("binge_sessions_count", 0)

        # Query vector store for distraction traces
        rabbit_holes = [r for r in self.vector_store.similarity_search("entertainment gaming memes comedy shorts kdrama", top_k=5) if r.get("score", 0) > 0.12]
        rabbit_titles = [r["metadata"].get("title") for r in rabbit_holes if r.get("metadata") and r["metadata"].get("category") in ["Gaming", "Entertainment", "Comedy", "Shorts"]]

        # Query vector store for learning traces
        learning_candidates = [r for r in self.vector_store.similarity_search("programming tutorial software education lecture coding algorithms", top_k=5) if r.get("score", 0) > 0.15]
        learning_titles = [r["metadata"].get("title") for r in learning_candidates if r.get("metadata") and r["metadata"].get("category") in ["Education", "Science & Technology", "Productivity"]]

        suggestions = []

        # Suggestion 1: Vulnerability Window & Trigger Intervention
        if peak_hour != "None":
            suggestions.append({
                "id": "vulnerability_guard",
                "badge": "Temporal Defense",
                "title": f"Protect Your Peak Distraction Window ({peak_hour})",
                "diagnosis": f"Your watch history shows your highest volume of distracting content occurs during {peak_hour}. At this time, willpower is low and autopilot browsing begins.",
                "prescription": f"Schedule an intentional non-screen buffer or a single 25-minute Pomodoro sprint at this hour. Close YouTube completely 15 minutes before {peak_hour}.",
                "links": [
                    {"label": "Use Pomofocus to timebox this critical window", "url": self.CURATED_RESOURCES["focus_timers"][0]["url"]},
                    {"label": "Install Unhook to strip YouTube's recommendation feed", "url": self.CURATED_RESOURCES["distraction_blockers"][0]["url"]}
                ]
            })

        # Suggestion 2: Curbing Binge Streaks
        if binge_count > 0 or distraction_pct >= 40:
            sample_binge = f" (e.g., '{rabbit_titles[0]}')" if rabbit_titles else ""
            suggestions.append({
                "id": "binge_breaker",
                "badge": "Impulse Control",
                "title": "Enforce Friction on Algorithmic Feeds",
                "diagnosis": f"You logged {distraction_pct}% distraction watch time with {binge_count} multi-video binge streaks{sample_binge}. Recommendation algorithms thrive on zero friction.",
                "prescription": "Introduce strict digital friction: ban autoplay, install feed blockers, and set up a 10-minute rule: if you want to watch entertainment, write down what you want to watch and wait 10 minutes first.",
                "links": [
                    {"label": "Deploy Cold Turkey Blocker to seal distracting URLs", "url": self.CURATED_RESOURCES["distraction_blockers"][1]["url"]},
                    {"label": "Study Huberman's Dopamine Reset Strategy", "url": self.CURATED_RESOURCES["deep_work"][1]["url"]}
                ]
            })

        # Suggestion 3: Convert Passive Consumption to Active Learning
        if learning_titles:
            sample_learn = f"'{learning_titles[0]}'"
            suggestions.append({
                "id": "active_learning_shift",
                "badge": "Active Execution",
                "title": "Shift from Tutorial Watching to Hands-On Building",
                "diagnosis": f"You're watching educational content like {sample_learn}, but passive video watching yields under 20% retention compared to coding directly.",
                "prescription": f"Adopt the 2:1 rule: for every 20 minutes of educational video watched, spend 40 minutes implementing what was taught without looking at the video.",
                "links": [
                    {"label": "Practice actively on freeCodeCamp Challenges", "url": self.CURATED_RESOURCES["active_learning"][0]["url"]},
                    {"label": "Cal Newport's Deep Work Rules", "url": self.CURATED_RESOURCES["deep_work"][0]["url"]}
                ]
            })
        else:
            suggestions.append({
                "id": "deep_work_foundation",
                "badge": "Deep Work",
                "title": "Establish 90-Minute Morning Monotasking",
                "diagnosis": "Unchecked distraction fragments attention and reduces cognitive bandwidth for hard tasks.",
                "prescription": f"Prioritize your declared goal: '{user_goal}'. Reserve the first 90 minutes of your workday for zero-multitasking deep work before opening any browser tabs.",
                "links": [
                    {"label": "Cal Newport's Deep Work Execution Framework", "url": self.CURATED_RESOURCES["deep_work"][0]["url"]},
                    {"label": "Freedom Website & App Blocker", "url": self.CURATED_RESOURCES["distraction_blockers"][2]["url"]}
                ]
            })

        # Suggestion 4: Evening Recovery vs Late-night Scrolling
        suggestions.append({
            "id": "evening_winddown",
            "badge": "Recovery Protocol",
            "title": "Hard Cutoff for Screens Before Bed",
            "diagnosis": "Late-night YouTube viewing spikes blue light and disrupts melatonin synthesis, causing low energy and higher distractibility the next morning.",
            "prescription": "Enforce an absolute screen shutdown 60 minutes before sleep. Switch to physical reading or journaling to recharge focus reserves for tomorrow.",
            "links": [
                {"label": "MIT OpenCourseWare Learning Library", "url": self.CURATED_RESOURCES["active_learning"][1]["url"]},
                {"label": "Forest Focus Gamification Tool", "url": self.CURATED_RESOURCES["focus_timers"][1]["url"]}
            ]
        })

        return {
            "summary": f"Your daily watch time is {total_time_fmt} ({distraction_pct}% distraction). Here is your tailored productivity roadmap:",
            "user_goal": user_goal,
            "distraction_pct": distraction_pct,
            "total_watch_time": total_time_fmt,
            "suggestions": suggestions
        }
