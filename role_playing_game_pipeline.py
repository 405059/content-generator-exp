import json
import os
import chat
import system_prompt


class RolePlayingGame:
    def __init__(self, game_root, game_name, game_id, enable_image_generation: bool):
        self.game_root = game_root
        self.game_name = game_name
        self.game_id = game_id
        self.enable_image_generation = enable_image_generation
        self.role_play_game_str = ""
        self.key_points_str = ""
        self.external_message = ""
        self.gender = "null"
        self.game_save_path = os.path.join(self.game_root, f"{self.game_name}_{self.game_id}")
        os.makedirs(self.game_save_path, exist_ok=True)
        
        if not self.enable_image_generation:
            print("Image generation disabled. Placeholder images will be generated.")

    def _create_placeholder_image(self, image_path: str):
        """
        Create a 720p white placeholder image.
        
        Args:
            image_path (str): Path to save the placeholder image.
        """
        from PIL import Image
        
        # Create 1280x720 white image
        placeholder = Image.new('RGB', (1280, 720), 'white')
        placeholder.save(image_path)

    def generate(self, pa_in_coda, complete_story):
        print("\n=== Starting Role-Playing Game Generation ===")
        
        print("Step 1/5: Extracting viewpoint statements...")
        contents = [item['content'] for item in pa_in_coda if 'content' in item and item.get('type') == 'PA']
        full_content = ' '.join(contents)
        key_point_seed = f"Story:{complete_story} Viewpoint Statement Sentences:{full_content}"
        
        print("Step 2/5: Generating key points from viewpoints...")
        # 替换: 使用 generate_text 替换 cached_chat_bot_format
        self.key_points_str = chat.generate_text(
            system_prompt=system_prompt.extract_key_points,
            user_prompt=key_point_seed
        ).strip()
        print("  ✓ Key points extracted successfully")

        key_points_dict = json.loads(chat.fix_json_response(self.key_points_str))
        # 假设我们总是处理第一个关键点
        key_point = key_points_dict["key_points"][0]
        print(f"  Core viewpoint: {key_point[:100]}..." if len(key_point) > 100 else f"  Core viewpoint: {key_point}")
        
        role_play_game_seed = (f"Core Viewpoint:{key_point},"
                               f"Number of Strategies:3")

        print("Step 3/5: Generating role-playing game scenarios...")
        # 替换: 使用 generate_text 替换 cached_chat_bot_format
        self.role_play_game_str = chat.generate_text(
            system_prompt=system_prompt.role_play_game_generation,
            user_prompt=role_play_game_seed
        )
        print("  ✓ Role-playing scenarios generated")

        role_play_game = json.loads(chat.fix_json_response(self.role_play_game_str))
        
        print("Step 4/5: Generating character portrait and external messages...")
        # 替换: 使用 generate_text 替换 cached_chat_bot_format
        self.external_message = chat.generate_text(
            system_prompt=system_prompt.role_play_external_message,
            user_prompt=f"Core Identity and Background:{role_play_game['Core Identity and Background']}"
        )
        print("  ✓ External messages generated")

        print("Step 5/5: Generating character portrait image...")
        self.role_playing_external_message_generate()
        print("  ✓ Character portrait saved")
        
        print("Saving role-playing game data...")
        result = self.save_formatted_rpg_data()
        print("=== Role-Playing Game Generation Complete! ===\n")
        return result

    def role_playing_external_message_generate(self):
        external_message_dict = json.loads(chat.fix_json_response(self.external_message))
        self.gender = external_message_dict.get("Gender", "null")
        image_prompts = external_message_dict["Character Portrait Illustration"]
        cover_path = os.path.join(self.game_save_path, "game_cover.png")
        if not os.path.exists(cover_path):
            if self.enable_image_generation:
                # Generate actual image using AI
                print("  Generating character portrait with AI...")
                chat.generate_image(
                    image_prompts["positive_prompt"],
                    image_prompts["negative_prompt"],
                    cover_path
                )
            else:
                # Generate white placeholder image
                print("  Creating placeholder character portrait...")
                self._create_placeholder_image(cover_path)
        else:
            print(f"  Character portrait already exists: {cover_path}")

    def save_formatted_rpg_data(self):
        game_message_path = os.path.join(self.game_save_path, "game_message.txt")
        with open(game_message_path, "w", encoding="utf-8") as file:
            file.write(self.role_play_game_str)

        command_path = os.path.join(self.game_save_path, "command.txt")
        command_content = {
            "code": "null",
            "mark": "default",
            "parameters": self.gender
        }
        with open(command_path, "w", encoding="utf-8") as file:
            json.dump(command_content, file, ensure_ascii=False, indent=4)