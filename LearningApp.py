# -*- coding: utf-8 -*-
import json
import os
import webbrowser
from datetime import datetime

from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import StringProperty, NumericProperty
from kivy.storage.jsonstore import JsonStore
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.list import OneLineListItem, TwoLineListItem
from kivymd.toast import toast

# Register OptionButton in the factory so we can do Factory.OptionButton(...)
Factory.register("OptionButton", cls=MDFillRoundFlatButton)

KV_PATH    = "app.kv"
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
STORE_PATH = os.path.join(os.path.dirname(__file__), "performance.json")

YOUTUBE_IDS = {
    # Math Grade 1
    ("math", 1, 1): "6Nlan2OO92M",   # Count 1–20 Sing-a-Long (≈1:00)
    ("math", 1, 2): "Ju3kQjmcH5g",   # What Is Place Value? (≈2:30)
    ("math", 1, 3): "rPVdItitgIU",   # Addition & Subtraction Facts to 10 (≈1:45)
    ("math", 1, 4): "Ux_kLd7qAcY",   # 2D Shapes for Kids (≈2:00)

    # Math Grade 2
    ("math", 2, 1): "q_yUC1NCFkE",   # Skip Count by 2s/5s/10s (≈1:20)
    ("math", 2, 2): "1ACa-NW8-TU",   # Hundreds, Tens & Ones Explained (≈2:10)
    ("math", 2, 3): "bcOK7pGri1c",   # Adding 2-Digit Numbers Without Regrouping (≈2:45)
    ("math", 2, 4): "eW2dRLyoyds",   # Intro to Multiplication for Kids (≈2:00)

    # English Grade 1
    ("english", 1, 1): "ZhfW6oLzFYI", # Phonic Alphabet Song (≈0:45)
    ("english", 1, 2): "gIZjrcG9pW0", # Top 100 Sight Words in 2 Minutes (≈2:00)
    ("english", 1, 3): "AbvySmoKefU", # CVC Words Practice (≈2:15)
    ("english", 1, 4): "avC53wsZiJA", # Prepositions for Kids (≈2:30)

    # English Grade 2
    ("english", 2, 1): "B5-y__faQrY", # What Are Rhyming Words? (≈0:30)
    ("english", 2, 2): "kWtMmRZDY-4", # Dolch Sight Words Grade 2 (≈2:15)
    ("english", 2, 3): "JaQB4XsZnoU", # Simple Sentences for Kids (≈2:45)
    ("english", 2, 4): "8irI5t3ZLPs", # Nouns & Verbs for Kids (≈2:00)
}


class LoginScreen(MDScreen):
    def do_login(self):
        uname = self.ids.username.text.strip()
        pwd   = self.ids.password.text.strip()
        if uname and pwd:
            self.manager.current = "home"
        else:
            toast("Please enter both username and password")


class HomeScreen(MDScreen):
    pass


class GradeScreen(MDScreen):
    subject = ""

    def set_subject(self, subj):
        self.subject = subj
        self.manager.current = "grade"

    def pick_grade(self, grade):
        mod = self.manager.get_screen("module")
        mod.subject = self.subject
        mod.grade   = grade
        self.manager.current = "module"


class ModuleScreen(MDScreen):
    subject = ""
    grade   = 0

    def on_pre_enter(self):
        lst = self.ids.module_list
        lst.clear_widgets()
        for m in range(1, 5):
            fname = f"{self.subject.lower()}_grade{self.grade}_module{m}.json"
            path  = os.path.join(DATA_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            title = data.get("title", f"Module {m}")
            desc  = data.get("description", "")
            item = TwoLineListItem(text=title, secondary_text=desc)
            item.module = m
            item.bind(on_release=self.pick_module)
            lst.add_widget(item)

    def pick_module(self, item):
        video = self.manager.get_screen("video")
        video.load_video(self.subject, self.grade, item.module)
        self.manager.current = "video"


class VideoScreen(MDScreen):
    subject    = StringProperty("")
    grade      = NumericProperty(0)
    module     = NumericProperty(0)
    youtube_id = StringProperty("")

    def load_video(self, subject, grade, module):
        self.subject    = subject
        self.grade      = grade
        self.module     = module
        self.youtube_id = YOUTUBE_IDS.get((subject.lower(), grade, module), "")
        # update the label directly
        self.ids.video_label.text = (
            f"Watch the video for {subject}  Grade {grade}  Module {module}"
        )

    def open_video(self):
        if not self.youtube_id:
            toast("No video available for this module")
            return
        url = f"https://www.youtube.com/watch?v={self.youtube_id}"
        # Force a new tab (new=2) so it actually comes up in front
        webbrowser.open(url, new=2)

    def proceed(self):
        quiz = self.manager.get_screen("quiz")
        quiz.load_questions(self.subject, self.grade, self.module)
        self.manager.current = "quiz"


class QuizScreen(MDScreen):
    questions     = []
    idx           = 0
    correct_count = 0
    subject       = ""
    grade         = 0
    module        = 0

    def load_questions(self, subject, grade, module):
        self.subject = subject
        self.grade   = grade
        self.module  = module
        fname = f"{subject.lower()}_grade{grade}_module{module}.json"
        path  = os.path.join(DATA_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.questions = data.get("questions", data) if isinstance(data, dict) else data
        self.idx           = 0
        self.correct_count = 0
        self.ids.next_button.disabled = True
        self.show_question()

    def show_question(self):
        q = self.questions[self.idx]
        self.ids.question_label.text = q["question"]
        box = self.ids.options_box
        box.clear_widgets()
        for opt in q["options"]:
            btn = Factory.OptionButton(text=opt)
            btn.bind(on_release=self.check_answer)
            box.add_widget(btn)
        self.ids.feedback.text = ""

    def check_answer(self, btn):
        correct = self.questions[self.idx]["answer"]
        if btn.text == correct:
            self.correct_count += 1
            self.ids.feedback.text = "[color=00C853]Correct![/color]"
        else:
            self.ids.feedback.text = f"[color=D50000]Oops — answer is {correct}[/color]"
        self.ids.next_button.disabled = False

    def next_question(self):
        self.idx += 1
        if self.idx < len(self.questions):
            self.ids.next_button.disabled = True
            self.show_question()
        else:
            self.ids.feedback.text = "🎉 You’ve completed this quiz!"
            self.ids.options_box.clear_widgets()
            self.ids.next_button.disabled = True
            self.record_performance()

    def record_performance(self):
        app = MDApp.get_running_app()
        ts  = datetime.now().isoformat()
        app.store.put(
            ts,
            subject=self.subject,
            grade=self.grade,
            module=self.module,
            correct=self.correct_count,
            total=len(self.questions),
            timestamp=ts,
        )


class PerformanceScreen(MDScreen):
    def on_pre_enter(self):
        lst = self.ids.perf_list
        lst.clear_widgets()
        app = MDApp.get_running_app()
        for key in sorted(app.store.keys(), reverse=True):
            rec    = app.store.get(key)
            module = rec.get("module", "?")
            text   = (
                f"{rec['timestamp'][:19]} — "
                f"{rec['subject']} G{rec['grade']} M{module}: "
                f"{rec['correct']}/{rec['total']}"
            )
            lst.add_widget(OneLineListItem(text=text))

    def back_home(self, *args):
        self.manager.current = "home"


class EduApp(MDApp):
    def build(self):
        self.store = JsonStore(STORE_PATH)
        return Builder.load_file(KV_PATH)


if __name__ == "__main__":
    EduApp().run()
