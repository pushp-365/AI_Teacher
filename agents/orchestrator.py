import os
import re
from agents.parser import parse_teacher_input
from agents.reprompter import refine_topic_data
from agents.script_writer import generate_script
from tools.ppt_tool import generate_ppt
from tools.quiz_tool import generate_quiz

class Orchestrator:
    def sanitize_folder_name(self, name: str) -> str:
        """Removes special characters to create a valid folder name."""
        return re.sub(r'[\/:*?"<>|]', '', name).strip().replace(" ", "_")

    def run(self):
        print("========================================")
        print("     AI LECTURE WORKFLOW BACKEND        ")
        print("========================================\n")

        # Step 1: Parse Prompt
        raw_prompt = input("Enter Teacher Prompt: ")
        print("\n[Step 1] Parsing Prompt...")
        topic_data = parse_teacher_input(raw_prompt)

        # Step 2: Interactive Review & Re-prompter Loop
        while True:
            print("\n[Step 2] Proposed Curriculum Plan:")
            print(f" - Topic: {topic_data.get('topic')}")
            print(f" - Duration: {topic_data.get('duration')}")
            print(f" - Audience: {topic_data.get('audience_level')}")
            print(f" - Goals: {', '.join(topic_data.get('key_goals', []))}")

            confirm = input("\nApprove plan? (y/n) or type changes: ").strip()
            if confirm.lower() in ['y', 'yes']:
                break
            elif confirm.lower() in ['n', 'no']:
                print("Execution cancelled.")
                return
            else:
                print("\n[Refining Plan] Updating parameters via Re-Prompter...")
                topic_data = refine_topic_data(topic_data, confirm)

        # Step 3: Project Folder Creation
        custom_folder = input("\nEnter Project Folder Name (press Enter to auto-generate from topic): ").strip()
        if not custom_folder:
            custom_folder = self.sanitize_folder_name(topic_data.get("topic", "Project_Output"))

        project_dir = os.path.join(os.getcwd(), custom_folder)
        os.makedirs(project_dir, exist_ok=True)
        print(f"\n📁 Saving all generated assets in: {project_dir}\n")

        # Define output paths inside the project folder
        ppt_path = os.path.join(project_dir, "Lecture_Package.pptx")
        quiz_path = os.path.join(project_dir, "Quiz.txt")
        script_path = os.path.join(project_dir, "Speaker_Script.txt")

        # Step 4: PPT & Image Tool
        print("[Step 4] Building Presentation & Rendering Graphics...")
        slides_content = generate_ppt(topic_data, output_filepath=ppt_path)

        # Step 5: Quiz Generator
        print("\n[Step 5] Generating Assessment Quiz...")
        generate_quiz(topic_data, output_filepath=quiz_path)

        # Step 6: Script Writer
        print("\n[Step 6] Writing Lecture Script & Speaker Notes...")
        generate_script(topic_data, slides_content, output_filepath=script_path)

        print(f"\n✅ Process Complete! All educational artifacts saved inside '{custom_folder}' folder.")