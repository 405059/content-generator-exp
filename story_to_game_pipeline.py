import chat
import system_prompt
import json
import re
import random
from typing import Any, Dict, Iterable, List, Union
from role_playing_game_pipeline import RolePlayingGame
from interactive_story_game_pipeline import InteractiveStoryGame


def load_story_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        lines = content.strip().split('\n')
        result = []
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            # Split by the first colon (considering content may also contain colons)
            if ':' in line:
                # Split into two parts: type and content
                parts = line.split(':', 1)  # Only split at the first colon
                line_type = parts[0].strip()
                line_content = parts[1].strip() if len(parts) > 1 else ""
                # Create dictionary
                line_dict = {
                    'type': line_type,
                    'content': line_content
                }
                result.append(line_dict)
            else:
                # If no colon, treat entire line as content with empty type
                line_dict = {
                    'type': '',
                    'content': line.strip()
                }
                result.append(line_dict)
        return result
    except FileNotFoundError:
        print(f"Error: File not found {file_path}")
        return []
    except Exception as e:
        print(f"Error occurred while reading file: {e}")
        return []


def concatenate_story_content(story_data):
    if not isinstance(story_data, list):
        raise ValueError("story_data parameter must be of list type")
    contents = [item.get('content', '') for item in story_data if isinstance(item, dict)]
    full_story = ' '.join(contents)
    return full_story


def extract_dmc(story_data):
    if not isinstance(story_data, list):
        raise ValueError("story_data parameter must be of list type")

    found_start = False
    found_end = False

    before_data = []
    branch_data = []
    after_data = []

    for item in story_data:
        if not isinstance(item, dict):
            continue

        current_type = item.get('type', '')

        if not found_start:
            if current_type == 'L3':
                found_start = True
                branch_data.append(item)
            else:
                before_data.append(item)
            continue

        if not found_end:
            if current_type == 'L6':
                found_end = True
                after_data.append(item)
            else:
                branch_data.append(item)
        else:
            after_data.append(item)

    if not found_start:
        return (
            "",
            concatenate_story_content(story_data),
            ""
        )

    return (
        concatenate_story_content(branch_data),
        concatenate_story_content(before_data),
        concatenate_story_content(after_data)
    )


def get_game_dmc_branch(story_branch):
    # 替换: 使用 generate_text 替换 cached_chat_bot_format
    dmc_branch_data = chat.generate_text(
        system_prompt=system_prompt.story_to_dmc,
        user_prompt=story_branch
    )
    branch_dict = json.loads(dmc_branch_data)
    decision_chain_list = branch_dict.get("decision_causality_chain", [])
    # Create a list to store all branch_json
    branch_json_list = []
    branch_id = 0
    for item in decision_chain_list:
        item_json = json.dumps(item, ensure_ascii=False, indent=2)
        # 替换: 使用 generate_text 替换 cached_chat_bot_format
        branch_json = chat.generate_text(
            system_prompt=system_prompt.dmc_to_branch,
            user_prompt=item_json
        )
        branch_json_list.append(branch_json)
        branch_id = branch_id + 1
    return branch_json_list


def pd_recognition(input_text):
    # 替换: 使用 generate_text 替换 cached_chat_bot_format
    raw_output = chat.generate_text(
        system_prompt=system_prompt.pd_recognition,
        user_prompt=input_text
    )
    labeled_segments = []
    for line in raw_output.splitlines():
        line = line.strip()
        if not line:
            continue
        if ':' not in line:
            continue
        seg_type, seg_content = line.split(':', 1)
        seg_type = seg_type.strip()
        seg_content = seg_content.strip()
        if seg_type and seg_content:
            labeled_segments.append((seg_type, seg_content))
    result = []
    cursor = 0
    for seg_type, seg_content in labeled_segments:
        index = input_text.find(seg_content, cursor)
        if index == -1:
            continue
        preceding = input_text[cursor:index]
        if preceding.strip():
            result.append({
                "content": preceding.strip(),
                "type": "null"
            })

        result.append({
            "content": seg_content.strip(),
            "type": seg_type
        })
        cursor = index + len(seg_content)

    trailing = input_text[cursor:]
    if trailing.strip():
        result.append({
            "content": trailing.strip(),
            "type": "null"
        })

    return result


def split_into_sentences(text):
    if not text:
        return []
    pattern = re.compile(r'[^。．\.！？!?]*[。．\.！？!?]')
    sentences = [match.strip() for match in pattern.findall(text) if match.strip()]
    remainder = pattern.sub('', text).strip()
    if remainder:
        sentences.append(remainder)
    return sentences


def check_story_integrity(raw_data: Iterable[Dict[str, Any]]) -> str:
    collected: List[Any] = []
    for item in raw_data:
        content = item.get("content")
        game_type = item.get("game_type")
        if game_type == "choice":
            parsed: Union[Dict[str, Any], None] = None
            if isinstance(content, dict):
                parsed = content
            elif isinstance(content, str):
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    parsed = None
            if isinstance(parsed, dict):
                if "scenarioDescription" in parsed:
                    next_scenario_list = parsed["next_scenario"]
                    collected_raw_data = (
                        f"{parsed['scenarioDescription']},"
                        f"{next_scenario_list[0]['choice']},"
                        f"Result:{next_scenario_list[0]['consequence']}"
                    )
                    collected.append(collected_raw_data)
                elif "question" in parsed:
                    collected.append(parsed["question"])
                else:
                    collected.append(None)
            else:
                collected.append(None)
        else:
            collected.append(content)
    return "".join(str(part) for part in collected if part is not None)


if __name__ == "__main__":
    """
    Program entry point:
    - Interactive Narrative (Text Adventure): Linear sentences (normal) of beforeMaterial + afterMaterial + DMC branches (choice)
    - PD: Only used for AI role-playing game generation, no longer expanded into branches.
    """

    # ================== Basic Path Configuration ==================
    STORY_FILE_PATH = "storyExample.txt"
    GAME_ROOT_PATH = r"D:\Users\Administrator\Desktop\aim"

    # ================== 1. Load Structured Story and Global Context ==================
    labov_structured_story = load_story_file(STORY_FILE_PATH)
    # Complete story context, used later as global reference input for LLM
    full_story_context = concatenate_story_content(labov_structured_story)
    # ================== 2. Extract DMC Section and Context ==================
    # branchNodeMaterial: DMC-related complex events and decision chains
    # beforeMaterial    : Summary and orientation section (EO) before DMC
    # afterMaterial     : Coda and evaluation section (PD area) after DMC
    branchNodeMaterial, beforeMaterial, afterMaterial = extract_dmc(labov_structured_story)
    # ================== 3. Build Interactive Narrative Sequence ==================
    # Note: Keep consistent with InteractiveStoryGame.generate expectations:
    # interactive_narrative_sequence is list[dict], not a dict with "entries".
    interactive_narrative_sequence: List[Dict[str, Any]] = []
    # Store story nodes in interactive_narrative_sequence according to their type and order
    for sentence in split_into_sentences(beforeMaterial):
        interactive_narrative_sequence.append({
            "content": sentence,
            "game_type": "normal"
        })
    dmc_branch_list = get_game_dmc_branch(branchNodeMaterial)
    for branch_str in dmc_branch_list:
        branch_content = branch_str.strip()
        if branch_content:
            interactive_narrative_sequence.append({
                "content": branch_content,
                "game_type": "choice"  # DMC decision branch
            })
    for sentence in split_into_sentences(afterMaterial):
        interactive_narrative_sequence.append({
            "content": sentence,
            "game_type": "normal"
        })
    pd_result = pd_recognition(afterMaterial)
    # ================== 5. Generate AI Role-Playing Game ==================
    role_playing_generator = RolePlayingGame(
        game_root=GAME_ROOT_PATH,
        game_name="default",
        game_id="0"
    )
    role_playing_generator.generate(
        pd_result,
        full_story_context
    )
    # ================== 6. Generate Interactive Narrative Text Adventure Game ==================
    game_generator = InteractiveStoryGame(
        game_root=GAME_ROOT_PATH,
        game_name="FactoryLeadership",
        game_id="1"
    )
    game_generator.generate(
        interactive_narrative_sequence,
        full_story_context
    )