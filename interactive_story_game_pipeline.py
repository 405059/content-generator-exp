import os
import json
import random
from typing import List, Dict, Any
import chat
import system_prompt


class InteractiveStoryGame:
    """
    Generate an interactive narrative game based on a series of narrative nodes.
    """

    def __init__(self, game_root: str, game_name: str, game_id: str):
        """
        Initialize the game generator.

        Args:
            game_root (str): Root directory for game storage.
            game_name (str): Game name.
            game_id (str): Unique game ID.
        """
        self.game_root = game_root
        self.game_name = game_name
        self.game_id = game_id

        # Construct game save path. All files (images, txt) will be stored in this directory.
        self.game_save_path = os.path.join(self.game_root, f"{self.game_name}_{self.game_id}")

        # Create main directory
        os.makedirs(self.game_save_path, exist_ok=True)

        print(f"Game '{self.game_name}' ({self.game_id}) will be saved at: {self.game_save_path}")

    def _get_image_prompt(self, input_act: str, raw_story_input: str, narrative_standards_str: str) -> Dict[str, str]:
        """
        Call LLM to generate image prompts for the given story segment.

        Args:
            input_act (str): Specific story content to be illustrated.
            raw_story_input (str): Complete original story context.
            narrative_standards_str (str): Determined art style description.

        Returns:
            Dict[str, str]: Dictionary containing "positive_prompt" and "negative_prompt".
        """
        user_input = (
            f"Story Content: {raw_story_input}\n"
            f"Determined Art Style: {narrative_standards_str}\n"
            f"Story Part to Be Illustrated: {input_act}"
        )

        # 替换: 使用 generate_text 替换 cached_chat_bot_format
        prompt_str = chat.generate_text(
            system_prompt=system_prompt.drawIllustration,
            user_prompt=user_input
        )
        
        try:
            return json.loads(prompt_str)
        except json.JSONDecodeError:
            print(f"Error: Unable to parse image prompt JSON: {prompt_str}")
            return {
                "positive_prompt": f"A scene depicting: {input_act}",
                "negative_prompt": "blurry, low quality"
            }

    def _generate_and_save_image(self, input_act: str, image_filename: str, raw_story_input: str,
                                 narrative_standards_str: str):
        """
        Generate and save image, skip if image already exists.

        Args:
            input_act (str): Text content for image generation.
            image_filename (str): Filename to save the image (e.g., 'img_0.png').
            raw_story_input (str): Complete story context.
            narrative_standards_str (str): Determined art style.
        """
        # Image is saved directly in the game main directory
        full_image_path = os.path.join(self.game_save_path, image_filename)

        if os.path.exists(full_image_path):
            print(f"Image {image_filename} already exists, skipping generation.")
            return

        # 1. Get image prompts
        image_prompt_dict = self._get_image_prompt(input_act, raw_story_input, narrative_standards_str)

        # 2. Generate image
        chat.generate_image(
            image_prompt_dict.get("positive_prompt", ""),
            image_prompt_dict.get("negative_prompt", ""),
            full_image_path
        )

    def _save_game_files(self, game_data: str):
        """
        Save final game data to files.

        Args:
            game_data (str): Formatted game data as a long string.
        """
        # 1. Save command.txt (according to user-specified new format)
        command_path = os.path.join(self.game_save_path, "command.txt")
        command_content = {
            "code": "null",
            "mark": "narrative",
            "parameters": "null"
        }
        with open(command_path, 'w', encoding='utf-8') as f:
            json.dump(command_content, f, ensure_ascii=False, indent=4)
        print(f"Saved command file: {command_path}")

        # 2. Save game_message.txt
        message_path = os.path.join(self.game_save_path, "game_message.txt")
        message_content = {
            "game_name": self.game_name,
            "game_description": "An interactive narrative game adapted from real conversations.",
            "game_data": game_data
        }
        with open(message_path, 'w', encoding='utf-8') as f:
            json.dump(message_content, f, ensure_ascii=False, indent=4)
        print(f"Saved game message file: {message_path}")

    def generate(self, narrative_raw_data: List[Dict[str, str]], raw_story_input: str):
        """
        Traverse narrative data to generate complete interactive game files.

        Args:
            narrative_raw_data (List[Dict[str, str]]): List containing story nodes and types.
            raw_story_input (str): Complete original story text for providing context.
        """
        print("--- Starting interactive narrative game generation ---")

        # Step 1: Determine unified art style for the entire story
        print("Determining story art style...")
        # 替换: 使用 generate_text 替换 cached_chat_bot_format
        narrative_standards_str = chat.generate_text(
            system_prompt=system_prompt.defineNarrativeStandards,
            user_prompt=raw_story_input
        )
        print(f"Art style determined: {narrative_standards_str}")

        game_data_parts = []
        image_counter = 0

        # Step 2: Traverse all narrative nodes
        for i, data_node in enumerate(narrative_raw_data):
            node_type = data_node.get("game_type")
            content = data_node.get("content")

            print(f"\nProcessing node {i + 1}/{len(narrative_raw_data)} - Type: {node_type}")

            if node_type == "normal":
                # --- C1 type: Normal narration ---
                input_act = content
                image_filename = f"img_{image_counter}.png"
                self._generate_and_save_image(input_act, image_filename, raw_story_input, narrative_standards_str)

                game_data_parts.append(f"narration*{input_act}*main^{image_filename}")
                image_counter += 1

            elif node_type == "choice":
                # --- C2/C3/C4 type: Choice ---
                try:
                    parsed_content = json.loads(content)
                except json.JSONDecodeError:
                    print(f"Error: Unable to parse choice node JSON content: {content}")
                    continue

                if "scenarioDescription" in parsed_content:
                    # --- C2 type: Decision choice, each consequence has independent image ---
                    question = parsed_content["scenarioDescription"]
                    options = parsed_content["next_scenario"]

                    question_image_filename = f"img_{image_counter}.png"
                    self._generate_and_save_image(question, question_image_filename, raw_story_input,
                                                  narrative_standards_str)
                    image_counter += 1

                    # Determine main branch: before shuffling order, record the first option's consequence
                    main_consequence_text = options[0]["consequence"]

                    random.shuffle(options)

                    choice_texts = [opt["choice"] for opt in options]
                    choice_str = f"choice*{question}%{'|'.join(choice_texts)}*main^{question_image_filename}"
                    game_data_parts.append(choice_str)

                    for opt in options:
                        consequence_text = opt["consequence"]
                        consequence_image_filename = f"img_{image_counter}.png"
                        self._generate_and_save_image(consequence_text, consequence_image_filename, raw_story_input,
                                                      narrative_standards_str)

                        branch_type = "main" if consequence_text == main_consequence_text else "other"

                        narration_str = f"narration*{consequence_text}*{branch_type}^{consequence_image_filename}"
                        game_data_parts.append(narration_str)
                        image_counter += 1

                elif "question" in parsed_content:
                    # --- C3/C4 type: Viewpoint choice, all consequences share one image ---
                    question = parsed_content["question"]
                    options = parsed_content["options"]

                    shared_image_filename = f"img_{image_counter}.png"
                    self._generate_and_save_image(question, shared_image_filename, raw_story_input,
                                                  narrative_standards_str)
                    image_counter += 1

                    # Determine main branch: before shuffling order, record the first option's consequence
                    main_consequence_text = options[0]["consequence"]

                    random.shuffle(options)

                    choice_texts = [opt["choice"] for opt in options]
                    choice_str = f"choice*{question}%{'|'.join(choice_texts)}*main^{shared_image_filename}"
                    game_data_parts.append(choice_str)

                    for opt in options:
                        consequence_text = opt["consequence"]
                        branch_type = "main" if consequence_text == main_consequence_text else "other"

                        narration_str = f"narration*{consequence_text}*{branch_type}^{shared_image_filename}"
                        game_data_parts.append(narration_str)
                else:
                    print(f"Warning: Unknown choice format: {content}")

        # Step 3: Combine all parts and save files
        final_game_data = "$".join(game_data_parts)
        self._save_game_files(final_game_data)

        print("\n--- Interactive narrative game generation complete! ---")
        return self.game_save_path