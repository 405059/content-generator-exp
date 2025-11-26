import json
import os
import chat
import system_prompt


class RolePlayingGame:
    def __init__(self, game_root, game_name, game_id):
        self.game_root = game_root
        self.game_name = game_name
        self.game_id = game_id
        self.role_play_game_str = ""
        self.key_points_str = ""
        self.external_message = ""
        self.gender = "null"
        self.game_save_path = os.path.join(self.game_root, f"{self.game_name}_{self.game_id}")
        os.makedirs(self.game_save_path, exist_ok=True)

    def generate(self, pa_in_coda, complete_story):
        contents = [item['content'] for item in pa_in_coda if 'content' in item and item.get('type') == 'PA']
        full_content = ' '.join(contents)
        key_point_seed = f"Story:{complete_story} Viewpoint Statement Sentences:{full_content}"
        
        # 替换: 使用 generate_text 替换 cached_chat_bot_format
        self.key_points_str = chat.generate_text(
            system_prompt=system_prompt.extract_key_points,
            user_prompt=key_point_seed
        ).strip()

        key_points_dict = json.loads(self.key_points_str)
        # 假设我们总是处理第一个关键点
        key_point = key_points_dict["key_points"][0]
        role_play_game_seed = (f"Core Viewpoint:{key_point},"
                               f"Number of Strategies:3")

        # 替换: 使用 generate_text 替换 cached_chat_bot_format
        self.role_play_game_str = chat.generate_text(
            system_prompt=system_prompt.role_play_game_generation,
            user_prompt=role_play_game_seed
        )

        role_play_game = json.loads(self.role_play_game_str)
        
        # 替换: 使用 generate_text 替换 cached_chat_bot_format
        self.external_message = chat.generate_text(
            system_prompt=system_prompt.role_play_external_message,
            user_prompt=f"Core Identity and Background:{role_play_game['Core Identity and Background']}"
        )

        self.role_playing_external_message_generate()
        return self.save_formatted_rpg_data()

    def role_playing_external_message_generate(self):
        external_message_dict = json.loads(self.external_message)
        self.gender = external_message_dict.get("Gender", "null")
        image_prompts = external_message_dict["Character Portrait Illustration"]
        cover_path = os.path.join(self.game_save_path, "game_cover.png")
        if not os.path.exists(cover_path):
            chat.generate_image(
                image_prompts["positive_prompt"],
                image_prompts["negative_prompt"],
                cover_path
            )

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